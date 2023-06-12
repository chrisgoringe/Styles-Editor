import gradio as gr
import modules.scripts as scripts
from modules import script_callbacks
from modules.shared import cmd_opts, opts, prompt_styles
import pandas as pd
import numpy as np
import os

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
  help_text = """
Styles with a name starting `xxxxx::` can be edited in separate additional style files (named `xxxxx.csv`, and stored in the extension's own subdirectory).

The `Extract` button will update any additional style files to reflect changes made while editing the master style file. To each additional style file (eg `Artists.csv`) 
will be added all styles with a name starting `Artists::`. Identically named styles will be replaced, other styles in the additional sheet are unchanged.

The `Merge` button will copy all additional styles (from all files) into the master sheet, with the appropriate prefix, 
and will *remove any styles containing :: which aren't present*.

You can create new additional style files using the `Create` button - the name you give the file will be the prefix.

Suggested workflow:
- Create additional style files for the categories you want to sort your styles into (eg `Artist`)
- Edit the main sheet to add `Artist::` to the start of the style name
- `Extract` the styles to get more manageable files to work with
- `Merge` the styles after making changes
"""
  cols = ['name','prompt','negative_prompt']
  full_cols = ['sort', 'name','prompt','negative_prompt']
  dataframe:pd.DataFrame = None
  dataeditor = None
  basedir = scripts.basedir()
  additional_style_files_directory = os.path.join(basedir,"additonal_style_files")
  try:
    default_style_file_path = cmd_opts.styles_file 
  except:
    default_style_file_path = getattr(opts, 'styles_dir', None)
  current_styles_file_path = default_style_file_path

  @classmethod
  def load_styles(cls):
    # skip the first line (which has headers) and use our own
    try:
      cls.dataframe = pd.read_csv(cls.current_styles_file_path, header=None, names=cls.cols, 
                                  engine='python', skiprows=[0], usecols=[0,1,2])
    except:
      cls.dataframe = pd.DataFrame(columns=cls.cols)
    cls.dataframe.insert(loc=0, column="sort", value=[i+1 for i in range(cls.dataframe.shape[0])])
    cls.dataframe.fillna('', inplace=True)
    cls.as_last_saved = cls.dataframe.to_numpy(copy=True)
    return cls.dataframe

  @staticmethod
  def to_numeric(series:pd.Series):
    nums = pd.to_numeric(series)
    if any(nums.isna()):
      raise Exception("don't update display")
    return nums

  @classmethod
  def save_styles(cls, data_to_save:pd.DataFrame, sort_first=False, filepath=None):
    update_display = True
    save_as = filepath or cls.current_styles_file_path
    if sort_first:
      try:
        dts = data_to_save.sort_values(by='sort', axis='index', inplace=False, na_position='first', key=cls.to_numeric)
        data_to_save = dts
      except:
        update_display = False
    if save_as:
      data_to_save = data_to_save.drop(index=[i for (i, row) in data_to_save.iterrows() if row[1]==''])
      data_to_save.to_csv(save_as, encoding="utf-8-sig", columns=cls.cols, index=False)
      if (save_as == cls.default_style_file_path):
        prompt_styles.reload()
    return data_to_save if update_display else gr.DataFrame.update()
  
  @classmethod
  def search_and_replace(cls, search:str, replace:str, current_data:pd.DataFrame):
    if len(search)==0:
      return current_data
    data_np = current_data.to_numpy()
    for i, row in enumerate(data_np):
      for j, item in enumerate(row):
        if isinstance(item,str) and search in item:
          data_np[i][j] = item.replace(search, replace)
    return pd.DataFrame(data=data_np, columns=cls.full_cols)

  @classmethod
  def relative(cls, filename):
    return os.path.relpath(os.path.join(cls.additional_style_files_directory,filename))
  
  @classmethod
  def use_additional_styles(cls, activate, filename):
    cls.current_styles_file_path = filename if activate else cls.default_style_file_path
    return gr.Row.update(visible=activate), cls.load_styles()
  
  @classmethod
  def additional_style_files(cls):
    if not os.path.exists(cls.additional_style_files_directory):
      os.mkdir(cls.additional_style_files_directory)
    return ['']+[cls.relative(f) for f in os.listdir(cls.additional_style_files_directory) if f.endswith(".csv")]
  
  @classmethod
  def create_style_file(cls, filename):
    if filename:
      filename = f"{os.path.splitext(filename)[0]}.csv"
      filepath = os.path.join(cls.additional_style_files_directory, filename)
      if not os.path.exists(filepath):
        print("", file=open(filepath,"w"))
      return gr.Dropdown.update(choices=cls.additional_style_files(), value=cls.relative(filename))
    return gr.Dropdown.update()
  
  @classmethod
  def select_style_file(cls, filepath):
    cls.current_styles_file_path = filepath
    return cls.load_styles() 
  
  @classmethod
  def merge_style_files(cls):
    purged = [row for row in cls.select_style_file(cls.default_style_file_path).to_numpy() if "::" not in row[1]]
    for filepath in cls.additional_style_files():
      prefix = os.path.splitext(os.path.split(filepath)[1])[0] + "::"
      for row in cls.select_style_file(filepath).to_numpy():
        row[1] = prefix + row[1]
        purged.append(row)
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
    prefixed_styles = [row for row in cls.select_style_file(cls.default_style_file_path).to_numpy() if "::" in row[1]]
    for filepath in cls.additional_style_files():
      prefix = os.path.splitext(os.path.split(filepath)[1])[0] + "::"
      additional_file_contents = cls.select_style_file(filepath).to_numpy()
      for prefixed_style in prefixed_styles:
        if prefixed_style[1].startswith(prefix):
          additional_file_contents = cls.add_or_replace(additional_file_contents, prefixed_style, prefix)
      cls.save_styles(pd.DataFrame(additional_file_contents, columns=cls.full_cols), filepath=filepath)
    cls.current_styles_file_path = None
    return gr.Dropdown.update(choices=cls.additional_style_files(), value=""), cls.load_styles()
  
  @classmethod
  def on_ui_tabs(cls):
    with gr.Blocks(analytics_enabled=False) as style_editor:
      dummy_component = gr.Label(visible=False)
      with gr.Row():
        with gr.Column(scale=1, min_width=100):
          cls.load_button = gr.Button(value="Reload Styles", elem_id="style_editor_load")
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
                cls.style_file_selection = gr.Dropdown(choices=cls.additional_style_files(), value="", label="Additional Style File to Edit")
              with gr.Column(scale=1, min_width=400):
                cls.create_additional_stylefile = gr.Button(value="Create new additional style file")
                cls.split_style_files_button = gr.Button(value="Extract from master")
                cls.merge_style_files_button = gr.Button(value="Merge into master")
              with gr.Column(scale=10):
                pass
            with gr.Row():
              with gr.Accordion(open=False, label="Help!"):
                gr.Markdown(value=cls.help_text)     
      with gr.Row():
        with gr.Column(scale=1, min_width=150):
          cls.autosort_checkbox = gr.Checkbox(value=False, label="Autosort")
        with gr.Column(scale=1, min_width=250):
          cls.fix_sort_column_button = gr.Button(value="Renumber sort columm")
        with gr.Column(scale=10):
          pass
      with gr.Row():
        cls.dataeditor = gr.Dataframe(value=cls.load_styles, col_count=(len(cls.cols)+1,'fixed'), 
                                          wrap=True, max_rows=1000, show_label=False, interactive=True, elem_id="style_editor_grid")

      cls.load_button.click(fn=cls.load_styles, outputs=cls.dataeditor)
      
      cls.search_and_replace_button.click(fn=cls.search_and_replace, inputs=[cls.search_box, cls.replace_box, cls.dataeditor], outputs=cls.dataeditor)

      cls.filter_box.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")
      cls.filter_select.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")

      cls.dataeditor.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")

      cls.dataeditor.input(fn=cls.save_styles, inputs=[cls.dataeditor, cls.autosort_checkbox], outputs=cls.dataeditor)
      cls.autosort_checkbox.change(fn=cls.save_styles, inputs=[cls.dataeditor, cls.autosort_checkbox], outputs=cls.dataeditor)
      cls.fix_sort_column_button.click(fn=cls.load_styles, outputs=cls.dataeditor)

      style_editor.load(fn=None, _js="when_loaded")

      cls.use_additional_styles_checkbox.change(fn=cls.use_additional_styles, inputs=[cls.use_additional_styles_checkbox, cls.style_file_selection], outputs=[cls.additional_file_display, cls.dataeditor])
      cls.create_additional_stylefile.click(fn=cls.create_style_file, inputs=dummy_component, outputs=cls.style_file_selection, _js="new_style_file_dialog")
      cls.style_file_selection.change(fn=cls.select_style_file, inputs=cls.style_file_selection, outputs=cls.dataeditor)
      cls.merge_style_files_button.click(fn=cls.merge_style_files, outputs=cls.use_additional_styles_checkbox)
      cls.split_style_files_button.click(fn=cls.extract_additional_styles, outputs=[cls.style_file_selection, cls.dataeditor])

    return [(style_editor, "Style Editor", "style_editor")]

script_callbacks.on_ui_tabs(StyleEditor.on_ui_tabs)