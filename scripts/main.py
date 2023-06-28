import gradio as gr
import modules.scripts as scripts
from modules import script_callbacks

import pandas as pd
import numpy as np
import os
from git import Repo
import json
import time, threading

from scripts.filemanager import FileManager

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
- Restore from backups

## Changed in recent updates:
- Option to encrypt backups
- Restored the `notes` column
- Automatically create new Additional Style Files if needed
- Automatically delete empty Additional Style Files on merge
- Regular backups created in `extensions/Styles-Editor/backups`
- Removed `Renumber Sort Column` button (just switch tabs and switch back!)
- Removed `Extract from Master` button (automatically done when you go into additional style files view)- Right-click can be used to select a row in the table (a style)
- Delete the selected style by pressing `backspace`/`delete`

"""
  display_columns = ['sort', 'name','prompt','negative_prompt','notes']
  githash = Repo(FileManager.basedir).git.rev_parse("HEAD")
  changed_since_backup = False
  backup_thread = None
  backup_delay = 600

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
      FileManager.save_styles(data)
    return data

  @classmethod
  def handle_dataeditor_input(cls, data:pd.DataFrame, autosort) -> pd.DataFrame:
    cls.changed_since_backup = True
    data = cls.drop_deleted(data)
    data = cls.sort_dataset(data) if autosort else data
    FileManager.save_styles(data)
    return data
  
  @classmethod
  def handle_search_and_replace_click(cls, search:str, replace:str, current_data:pd.DataFrame):
    if len(search)==0:
      return current_data
    data_np = current_data.to_numpy()
    for i, row in enumerate(data_np):
      for j, item in enumerate(row):
        if isinstance(item,str) and search in item:
          data_np[i][j] = item.replace(search, replace)
    return pd.DataFrame(data=data_np, columns=cls.display_columns)
  
  @classmethod
  def handle_use_additional_styles_box_change(cls, activate, filename):
    FileManager.current_styles_file_path = FileManager.full_path(filename) if activate else FileManager.default_style_file_path
    if activate:
      cls.extract_additional_styles()
      labels = cls.additional_style_files(display_names=True, include_blank=False)
      selected = FileManager.display_name(FileManager.current_styles_file_path)
      selected = selected if selected in labels else labels[0] if len(labels)>0 else ''
      return gr.Row.update(visible=activate), FileManager.load_styles(), gr.Dropdown.update(choices=labels, value=selected)
    else:
      return gr.Row.update(visible=activate), FileManager.load_styles(), gr.Dropdown.update()
  
  @classmethod
  def additional_style_files(cls, include_blank=True, display_names=False):
    format = FileManager.display_name if display_names else FileManager.full_path
    asf = [format(f) for f in os.listdir(FileManager.additional_style_files_directory) if f.endswith(".csv")]
    return [format('')]+asf if include_blank else asf
  
  @classmethod
  def handle_create_additional_style_file_click(cls, name):
    FileManager.create_file_if_missing(name)
    return gr.Dropdown.update(choices=cls.additional_style_files(display_names=True), value=FileManager.display_name(name))
  
  @classmethod
  def handle_style_file_selection_change(cls, filepath):
    FileManager.current_styles_file_path = FileManager.full_path(filepath)
    return FileManager.load_styles() 
  
  @classmethod
  def handle_merge_style_files_click(cls):
    purged = [row for row in FileManager.load_styles(FileManager.default_style_file_path).to_numpy() if "::" not in row[1]]
    for filepath in cls.additional_style_files(include_blank=False):
      rows = FileManager.load_styles(filepath).to_numpy()
      if len(rows)>0:
        prefix = FileManager.display_name(filepath) + "::"
        for row in rows:
          row[1] = prefix + row[1]
          purged.append(row)
      else:
        os.remove(filepath)
    new_df = pd.DataFrame(purged, columns=cls.display_columns)
    FileManager.save_styles(new_df, use_default=True)
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
    prefixed_styles = [row for row in FileManager.load_styles(use_default=True).to_numpy() if "::" in row[1]]
    for prefix in {row[1][:row[1].find('::')] for row in prefixed_styles}:
      FileManager.create_file_if_missing(prefix)
    for filepath in cls.additional_style_files(include_blank=False):
      prefix = os.path.splitext(os.path.split(filepath)[1])[0] + "::"
      additional_file_contents = FileManager.load_styles(FileManager.full_path(filepath)).to_numpy()
      for prefixed_style in prefixed_styles:
        if prefixed_style[1].startswith(prefix):
          additional_file_contents = cls.add_or_replace(additional_file_contents, prefixed_style, prefix)
      FileManager.save_styles(pd.DataFrame(additional_file_contents, columns=cls.display_columns), filename=filepath)
  
  @classmethod
  def get_and_update_lasthash(cls) -> str:
    try:
      with open(os.path.join(FileManager.basedir, "lasthash.json")) as f:
        lasthash = json.load(f)['lasthash']
    except:
      lasthash = ""
    print(json.dumps({"lasthash":cls.githash}),file=open(os.path.join(FileManager.basedir, "lasthash.json"), 'w'))
    return lasthash
  
  @classmethod
  def start_backups(cls):
    if cls.backup_thread is None:
      cls.backup_thread = threading.Thread(group=None, target=cls.handle_backup, daemon=True)
      cls.backup_thread.start()

  @classmethod
  def handle_backup(cls):
    while True:
      if cls.changed_since_backup:
        FileManager.do_backup()
        cls.changed_since_backup = False
      time.sleep(cls.backup_delay)

  @classmethod
  def handle_use_encryption_checkbox_changed(cls, encrypt):
    FileManager.encrypt = encrypt

  @classmethod
  def handle_encryption_key_change(cls, key):
    FileManager.encrypt_key = key

  @classmethod
  def handle_restore_backup_file_upload(cls, tempfile):
    if FileManager.restore_from_backup(tempfile.name):
      cls.extract_additional_styles()
      return gr.Text.update(visible=False), False, FileManager.load_styles(use_default=True)
    else:
      return gr.Text.update(visible=True, value="Couldn't restore for some reason")

  @classmethod
  def on_ui_tabs(cls):
    with gr.Blocks(analytics_enabled=False) as style_editor:
      dummy_component = gr.Label(visible=False)
      with gr.Row():
        with gr.Column(scale=1, min_width=600):
          with gr.Accordion(label="Documentation and Recent Changes", open=(cls.get_and_update_lasthash()!=cls.githash)):
            gr.HTML(value="<a href='https://github.com/chrisgoringe/Styles-Editor/blob/main/readme.md' target='_blank'>Link to Documentation</a>")
            gr.Markdown(value=cls.update_help)
            gr.HTML(value="<a href='https://github.com/chrisgoringe/Styles-Editor/blob/main/changes.md' target='_blank'>Change log</a>")
        with gr.Column(scale=1, min_width=500):
          with gr.Accordion(label="Encryption", open=False):
            cls.use_encryption_checkbox = gr.Checkbox(value=False, label="Use Encryption")
            cls.encryption_key_textbox = gr.Textbox(max_lines=1, placeholder="encryption key", label="Encryption Key")
            gr.Markdown(value="If checked, Backups are encrypted. The active style file and additional style files are not.")
            gr.Markdown(value="Files are encrypted using pyAesCrypt (https://pypi.org/project/pyAesCrypt/)")
          with gr.Accordion(label="Restore from Backup", open=False):
            cls.restore_backup_file_upload = gr.File(file_types=[".csv", ".aes"], label="Restore from backup")
            cls.restore_result = gr.Text(visible=False, show_label=False)
        with gr.Column(scale=10):
          pass
      with gr.Row():
        with gr.Column(scale=3, min_width=100):
          cls.filter_textbox = gr.Textbox(max_lines=1, interactive=True, placeholder="filter", elem_id="style_editor_filter", show_label=False)
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
                cls.style_file_selection = gr.Dropdown(choices=cls.additional_style_files(display_names=True), value=FileManager.display_name(''), 
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
        cls.dataeditor = gr.Dataframe(value=FileManager.load_styles, col_count=(len(cls.display_columns),'fixed'), 
                                          wrap=True, max_rows=1000, show_label=False, interactive=True, elem_id="style_editor_grid")
      
      cls.search_and_replace_button.click(fn=cls.handle_search_and_replace_click, inputs=[cls.search_box, cls.replace_box, cls.dataeditor], outputs=cls.dataeditor)

      cls.filter_textbox.change(fn=None, inputs=[cls.filter_textbox, cls.filter_select], _js="filter_style_list")
      cls.filter_select.change(fn=None, inputs=[cls.filter_textbox, cls.filter_select], _js="filter_style_list")

      cls.use_encryption_checkbox.change(fn=cls.handle_use_encryption_checkbox_changed, inputs=[cls.use_encryption_checkbox], outputs=[])
      cls.encryption_key_textbox.change(fn=cls.handle_encryption_key_change, inputs=[cls.encryption_key_textbox], outputs=[])
      cls.restore_backup_file_upload.upload(fn=cls.handle_restore_backup_file_upload, inputs=[cls.restore_backup_file_upload], outputs=[cls.restore_result, cls.use_additional_styles_checkbox, cls.dataeditor])

      cls.dataeditor.change(fn=None, inputs=[cls.filter_textbox, cls.filter_select], _js="filter_style_list")

      cls.dataeditor.input(fn=cls.handle_dataeditor_input, inputs=[cls.dataeditor, cls.autosort_checkbox], outputs=cls.dataeditor)
      cls.autosort_checkbox.change(fn=cls.handle_autosort_checkbox_change, inputs=[cls.dataeditor, cls.autosort_checkbox], outputs=cls.dataeditor)

      style_editor.load(fn=None, _js="when_loaded")
      style_editor.load(fn=cls.start_backups, inputs=[], outputs=[])

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
                tab.select(fn=FileManager.load_styles, outputs=cls.dataeditor)
                cls.tab = tab
              elif tab.id=="txt2img" or tab.id=="img2img":
                tab.select(fn=None, inputs=tab, _js="press_refresh_button")

script_callbacks.on_ui_tabs(StyleEditor.on_ui_tabs)
script_callbacks.on_app_started(StyleEditor.on_app_started)