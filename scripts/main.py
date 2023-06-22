import gradio as gr
import modules.scripts as scripts
from modules import script_callbacks
from modules.shared import cmd_opts, opts, prompt_styles
import pandas as pd
import numpy as np
import os
from git import Repo
import json
import shutil
import datetime
from pathlib import Path
try:
  import pyAesCrypt
  encrypt = True
except:
  encrypt = False

class Script(scripts.Script):
  def __init__(self) -> None:
    super().__init__()

  def title(self):
    return "Style Editor"

  def show(self, is_img2img):
    return scripts.AlwaysVisible

  def ui(self, is_img2img):
    return ()
  
class StyleEditor:
  update_help = """# Recent changes:
## Changed in this update:
- Option to swap style sets (master and additional files)
- Option to encrypt style set not being used
- Option to encrypt backups

## Changed in recent updates:
- Restored the `notes` column
- Automatically create new Additional Style Files if needed
- Automatically delete empty Additional Style Files on merge
- Regular backups created in `extensions/Styles-Editor/backups`
- Removed `Renumber Sort Column` button (just switch tabs and switch back!)
- Removed `Extract from Master` button (automatically done when you go into additional style files view)- Right-click can be used to select a row in the table (a style)
- Delete the selected style by pressing `backspace`/`delete`

"""
  cols = ['name','prompt','negative_prompt']
  full_cols = ['sort', 'name','prompt','negative_prompt','notes']
  dataeditor = None
  basedir = scripts.basedir()
  githash = Repo(basedir).git.rev_parse("HEAD")
  additional_style_files_directory = os.path.join(basedir,"additonal_style_files")
  backup_directory = os.path.join(basedir,"backups")
  if not os.path.exists(additional_style_files_directory):
    os.mkdir(additional_style_files_directory)
  if not os.path.exists(backup_directory):
    os.mkdir(backup_directory)
  try:
    default_style_file_path = cmd_opts.styles_file 
  except:
    default_style_file_path = getattr(opts, 'styles_dir', None)
  current_styles_file_path = default_style_file_path
  changed_since_backup = True
  try:
    with open(os.path.join(basedir, "notes.json")) as f:
      notes_dictionary = json.load(f)
  except:
    notes_dictionary = {}
  encrypt = False
  encrypt_key = ""
  
  @classmethod
  def save_notes_dictionary(cls):
    print(json.dumps(cls.notes_dictionary),file=open(os.path.join(cls.basedir, "notes.json"), 'w'))   

  @classmethod
  def update_notes_dictionary(cls, data:pd.DataFrame, prefix:str):
    for row in data.iterrows():
      stylename = prefix+"::"+row[1][1] if prefix!='' else row[1][1]
      cls.notes_dictionary[stylename] = row[1][4]

  @classmethod
  def lookup_notes(cls, stylename, prefix):
    stylename = prefix+"::"+stylename if prefix!='' else stylename
    return cls.notes_dictionary[stylename] if stylename in cls.notes_dictionary else ''

  @classmethod
  def load_styles(cls, file=None):
    # skip the first line (which has headers) and use our own
    file = file or cls.current_styles_file_path
    try:
      dataframe = pd.read_csv(file, header=None, names=cls.cols, 
                                  engine='python', skiprows=[0], usecols=[0,1,2])
    except:
      dataframe = pd.DataFrame(columns=cls.cols)
    display = cls.display_name(file)
    entries = range(dataframe.shape[0])
    dataframe.insert(loc=0, column="sort", value=[i+1 for i in entries])
    dataframe.insert(loc=4, column="notes", value=[cls.lookup_notes(dataframe['name'][i], display) for i in entries])
    dataframe.fillna('', inplace=True)
    return dataframe

  @staticmethod
  def to_numeric(series:pd.Series):
    nums = pd.to_numeric(series)
    if any(nums.isna()):
      raise Exception("don't update display")
    return nums
  
  @classmethod
  def sort_dataset(cls, data:pd.DataFrame) -> pd.DataFrame:
      try:
        return data.sort_values(by='sort', axis='index', inplace=False, na_position='first', key=cls.to_numeric)
      except:
        return data
      
  @classmethod
  def drop_deleted(cls, data:pd.DataFrame) -> pd.DataFrame:
    rows_to_drop = [i for (i, row) in data.iterrows() if row[0]=='!!!']
    return data.drop(index=rows_to_drop)
      
  @classmethod
  def handle_autosort_checkbox_change(cls, data:pd.DataFrame, autosort) -> pd.DataFrame:
    if autosort:
      data = cls.sort_dataset(data)
      cls.save_styles(data)
    return data

  @classmethod
  def handle_dataeditor_input(cls, data:pd.DataFrame, autosort) -> pd.DataFrame:
    cls.changed_since_backup = True
    data = cls.drop_deleted(data)
    data = cls.sort_dataset(data) if autosort else data
    cls.save_styles(data)
    return data
  
  @classmethod
  def save_styles(cls, data:pd.DataFrame, filepath=None):
    save_as = filepath or cls.current_styles_file_path
    data.to_csv(save_as, encoding="utf-8-sig", columns=cls.cols, index=False)
    if (save_as == cls.default_style_file_path):
      prompt_styles.reload()
    cls.update_notes_dictionary(data, cls.display_name(save_as))
    cls.save_notes_dictionary()

  @classmethod
  def handle_search_and_replace_click(cls, search:str, replace:str, current_data:pd.DataFrame):
    if len(search)==0:
      return current_data
    data_np = current_data.to_numpy()
    for i, row in enumerate(data_np):
      for j, item in enumerate(row):
        if isinstance(item,str) and search in item:
          data_np[i][j] = item.replace(search, replace)
    return pd.DataFrame(data=data_np, columns=cls.full_cols)

  @classmethod
  def full_path(cls, filename:str) -> str:
    """
    Return the full path for an additional style file.
    Input can be the full path, the filename with extension, or the filename without extension.
    If input is None, '', or the default style file path, return the default style file path
    """
    if filename is None or filename=='' or filename==cls.default_style_file_path:
      return cls.default_style_file_path
    filename = filename+".csv" if not filename.endswith(".csv") else filename
    return os.path.relpath(os.path.join(cls.additional_style_files_directory,os.path.split(filename)[1]))
                           
  @classmethod
  def display_name(cls, filename:str) -> str:
    """
    Return the full path for an additional style file. 
    Input can be the full path, the filename with extension, or the filename without extension
    """
    fullpath = cls.full_path(filename)
    return os.path.splitext(os.path.split(fullpath)[1])[0] if fullpath!=cls.default_style_file_path else ''
  
  @classmethod
  def handle_use_additional_styles_box_change(cls, activate, filename):
    cls.current_styles_file_path = cls.full_path(filename) if activate else cls.default_style_file_path
    if activate:
      cls.extract_additional_styles()
      labels = cls.additional_style_files(display_names=True, include_blank=False)
      selected = cls.display_name(cls.current_styles_file_path)
      selected = selected if selected in labels else labels[0] if len(labels)>0 else ''
      return gr.Row.update(visible=activate), cls.load_styles(), gr.Dropdown.update(choices=labels, value=selected)
    else:
      return gr.Row.update(visible=activate), cls.load_styles(), gr.Dropdown.update()
  
  @classmethod
  def additional_style_files(cls, include_blank=True, display_names=False):
    format = cls.display_name if display_names else cls.full_path
    asf = [format(f) for f in os.listdir(cls.additional_style_files_directory) if f.endswith(".csv")]
    return [format('')]+asf if include_blank else asf
  
  @classmethod
  def create_file_if_missing(cls, filename):
    filename = cls.full_path(filename)
    if not os.path.exists(filename):
      print("", file=open(filename,"w"))

  @classmethod
  def handle_create_additional_style_file_click(cls, name):
    cls.create_file_if_missing(name)
    return gr.Dropdown.update(choices=cls.additional_style_files(display_names=True), value=cls.display_name(name))
  
  @classmethod
  def handle_style_file_selection_change(cls, filepath):
    cls.current_styles_file_path = cls.full_path(filepath)
    return cls.load_styles() 
  
  @classmethod
  def handle_merge_style_files_click(cls):
    purged = [row for row in cls.load_styles(cls.default_style_file_path).to_numpy() if "::" not in row[1]]
    for filepath in cls.additional_style_files(include_blank=False):
      rows = cls.load_styles(filepath).to_numpy()
      if len(rows)>0:
        prefix = cls.display_name(filepath) + "::"
        for row in rows:
          row[1] = prefix + row[1]
          purged.append(row)
      else:
        os.remove(filepath)
    new_df = pd.DataFrame(purged, columns=cls.full_cols)
    cls.save_styles(new_df, filepath=cls.default_style_file_path)
    return False
  
  @staticmethod
  def add_or_replace(array:np.ndarray, row, prefix:str):
    row[1] = row[1][len(prefix):]
    for i in range(len(array)):
      if array[i][1] == row[1]:
        array[i] = row
        return array
    return np.vstack([array,row])

  @classmethod
  def extract_additional_styles(cls):
    prefixed_styles = [row for row in cls.load_styles(cls.default_style_file_path).to_numpy() if "::" in row[1]]
    for prefix in {row[1][:row[1].find('::')] for row in prefixed_styles}:
      cls.create_file_if_missing(prefix)
    for filepath in cls.additional_style_files(include_blank=False):
      prefix = os.path.splitext(os.path.split(filepath)[1])[0] + "::"
      additional_file_contents = cls.load_styles(cls.full_path(filepath)).to_numpy()
      for prefixed_style in prefixed_styles:
        if prefixed_style[1].startswith(prefix):
          additional_file_contents = cls.add_or_replace(additional_file_contents, prefixed_style, prefix)
      cls.save_styles(pd.DataFrame(additional_file_contents, columns=cls.full_cols), filepath=filepath)
  
  @classmethod
  def get_and_update_lasthash(cls) -> str:
    try:
      with open(os.path.join(cls.basedir, "lasthash.json")) as f:
        lasthash = json.load(f)['lasthash']
    except:
      lasthash = ""
    print(json.dumps({"lasthash":cls.githash}),file=open(os.path.join(cls.basedir, "lasthash.json"), 'w'))
    return lasthash
  
  @classmethod
  def do_backup(cls):
    if not cls.changed_since_backup:
      return
    fileroot = os.path.join(cls.backup_directory, datetime.datetime.now().strftime("%y%m%d_%H%M"))
    shutil.copyfile(cls.default_style_file_path, fileroot+".csv")
    shutil.make_archive(fileroot,format="zip",root_dir=cls.additional_style_files_directory,base_dir='.')
    paths = sorted(Path(cls.backup_directory).iterdir(), key=os.path.getmtime, reverse=True)
    for path in paths[24:]:
      os.remove(str(path))
    cls.changed_since_backup = False
    if cls.encrypt and len(cls.encrypt_key)>0:
      for extension in [".csv",".zip"]:
        pyAesCrypt.encryptFile(fileroot+extension, fileroot+extension+".aes", cls.encrypt_key)
        os.remove(fileroot+extension)

  @classmethod
  def handle_use_encryption_checkbox_changed(cls, encrypt):
    cls.encrypt = encrypt

  @classmethod
  def handle_encryption_key_change(cls, key):
    cls.encrypt_key = key

  @classmethod
  def on_ui_tabs(cls):
    with gr.Blocks(analytics_enabled=False) as style_editor:
      dummy_component = gr.Label(visible=False)
      with gr.Row():
        with gr.Column(scale=1, min_width=500):
          with gr.Accordion(label="Documentation and Recent Changes", open=(cls.get_and_update_lasthash()!=cls.githash)):
            gr.HTML(value="<a href='https://github.com/chrisgoringe/Styles-Editor/blob/main/readme.md' target='_blank'>Link to Documentation</a>")
            gr.Markdown(value=cls.update_help)
            gr.HTML(value="<a href='https://github.com/chrisgoringe/Styles-Editor/blob/main/changes.md' target='_blank'>Change log</a>")
        with gr.Column(scale=1, min_width=500):
          with gr.Accordion(label="Encryption", open=False):
            cls.use_encryption_checkbox = gr.Checkbox(value=False, label="Use Encryption")
            cls.encryption_key = gr.Textbox(max_lines=1, placeholder="encryption key", label="Encryption Key")
            gr.Markdown(value="Backups and inactive style sets are encrypted. The active style file and additional style files are not.")
            gr.Markdown(value="Files are encrypted using pyAesCrypt (https://pypi.org/project/pyAesCrypt/)")
        with gr.Column(scale=10):
          pass
      with gr.Row():
        with gr.Column(scale=3, min_width=100):
          cls.filter_box = gr.Textbox(max_lines=1, interactive=True, placeholder="filter", elem_id="style_editor_filter", show_label=False)
          cls.filter_select = gr.Dropdown(choices=["Exact match", "Case insensitive", "regex"], value="Exact match", show_label=False)
        with gr.Column(scale=2, min_width=100):
          cls.search_box = gr.Textbox(max_lines=1, interactive=True, placeholder="search for", show_label=False)
          cls.replace_box= gr.Textbox(max_lines=1, interactive=True, placeholder="replace with", show_label=False)
          cls.search_and_replace_button = gr.Button(value="Search and Replace")
      with gr.Row():
        with gr.Column():
          with gr.Row():
            cls.use_additional_styles_checkbox = gr.Checkbox(value=False, label="Edit additional style files")
          with gr.Group(visible=False) as cls.additional_file_display:
            with gr.Row():
              with gr.Column(scale=1, min_width=400):
                cls.style_file_selection = gr.Dropdown(choices=cls.additional_style_files(display_names=True), value=cls.display_name(''), 
                                                       label="Additional Style File")
              with gr.Column(scale=1, min_width=400):
                cls.create_additional_stylefile = gr.Button(value="Create new additional style file")
                cls.merge_style_files_button = gr.Button(value="Merge into master")
              with gr.Column(scale=10):
                pass
      with gr.Row():
        with gr.Column(scale=1, min_width=150):
          cls.autosort_checkbox = gr.Checkbox(value=False, label="Autosort")
        with gr.Column(scale=10):
          pass
      with gr.Row():
        cls.dataeditor = gr.Dataframe(value=cls.load_styles, col_count=(len(cls.full_cols),'fixed'), 
                                          wrap=True, max_rows=1000, show_label=False, interactive=True, elem_id="style_editor_grid")
      
      cls.search_and_replace_button.click(fn=cls.handle_search_and_replace_click, inputs=[cls.search_box, cls.replace_box, cls.dataeditor], outputs=cls.dataeditor)

      cls.filter_box.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")
      cls.filter_select.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")

      cls.use_encryption_checkbox.change(fn=cls.handle_use_encryption_checkbox_changed, inputs=[cls.use_encryption_checkbox], outputs=[])
      cls.encryption_key.change(fn=cls.handle_encryption_key_change, inputs=[cls.encryption_key], outputs=[])

      cls.dataeditor.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")

      cls.dataeditor.input(fn=cls.handle_dataeditor_input, inputs=[cls.dataeditor, cls.autosort_checkbox], outputs=cls.dataeditor)
      cls.autosort_checkbox.change(fn=cls.handle_autosort_checkbox_change, inputs=[cls.dataeditor, cls.autosort_checkbox], outputs=cls.dataeditor)

      style_editor.load(fn=None, _js="when_loaded")
      style_editor.load(fn=cls.do_backup, inputs=[], outputs=[], every=600)

      cls.use_additional_styles_checkbox.change(fn=cls.handle_use_additional_styles_box_change, inputs=[cls.use_additional_styles_checkbox, cls.style_file_selection], 
                                                outputs=[cls.additional_file_display, cls.dataeditor, cls.style_file_selection])
      cls.create_additional_stylefile.click(fn=cls.handle_create_additional_style_file_click, inputs=dummy_component, outputs=cls.style_file_selection, _js="new_style_file_dialog")
      cls.style_file_selection.change(fn=cls.handle_style_file_selection_change, inputs=cls.style_file_selection, outputs=cls.dataeditor)
      cls.merge_style_files_button.click(fn=cls.handle_merge_style_files_click, outputs=cls.use_additional_styles_checkbox)

    return [(style_editor, "Style Editor", "style_editor")]

  @classmethod
  def on_app_started(cls, block, fastapi):
    with block:
      for tabs in block.children:
        if isinstance(tabs, gr.layouts.Tabs):
          for tab in tabs.children:
            if isinstance(tab, gr.layouts.Tab):
              if tab.id=="style_editor":
                tab.select(fn=cls.load_styles, outputs=cls.dataeditor)
                cls.tab = tab
              elif tab.id=="txt2img" or tab.id=="img2img":
                tab.select(fn=None, inputs=tab, _js="press_refresh_button")

script_callbacks.on_ui_tabs(StyleEditor.on_ui_tabs)
script_callbacks.on_app_started(StyleEditor.on_app_started)