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
  help_text = """Categories (aka additional style files) are a way of breaking up a large style file.

Any style with a name of the form `category::style-name` is in category `category`.
"""
  cols = ['name','prompt','negative_prompt']
  full_cols = ['sort', 'name','prompt','negative_prompt']
  dataframe:pd.DataFrame = None
  dataeditor = None
  category = None
  categories_extracted = False

  @classmethod 
  def load_style_file(cls, category=None) -> pd.DataFrame:
    try:
      df = pd.read_csv(Categories.filename_to_use(category),# engine='python',
                       header=None, names=cls.cols, skiprows=[0], usecols=[0,1,2])
    except:
      df = pd.DataFrame(columns=cls.cols)
    df.insert(loc=0, column="sort", value=[i+1 for i in range(df.shape[0])])
    df.fillna('', inplace=True)
    return df
    
  @classmethod
  def load_styles(cls):
    cls.dataframe = cls.load_style_file(cls.category)
    cls.as_last_saved = cls.dataframe.to_numpy(copy=True)
    return gr.DataFrame.update(value=cls.dataframe, label=(cls.category or "All Styles"))

  @staticmethod
  def to_numeric(series:pd.Series):
    nums = pd.to_numeric(series)
    if any(nums.isna()):
      raise Exception("don't update display")
    return nums

  @classmethod
  def save_styles(cls, data_to_save:pd.DataFrame, category=None):
    category = category or cls.category
    data_to_return = data_to_save.drop(index=[i for (i, row) in data_to_save.iterrows() if row[1]=='' and (row[2]!='' or row[3]!='')])
    data_to_save = data_to_save.drop(index=[i for (i, row) in data_to_save.iterrows() if row[1]==''])
    data_to_save.to_csv(Categories.filename_to_use(category), encoding="utf-8-sig", columns=cls.cols, index=False)
    if category is not None and category is not Categories.everything_category and cls.categories_extracted:
      cls.merge_category_files()
    prompt_styles.reload()
    return data_to_return
  
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
  def view_by_category_changed(cls, activate, category):
    cls.category = category if activate else None
    if activate:
      cls.extract_category_files()
    return gr.Row.update(visible=activate), gr.Dropdown.update(choices=Categories.list_categories(), value=cls.category), cls.load_styles()
  
  @classmethod
  def create_category(cls, category):
    Categories.add_category(category)
    cls.category = category
    return gr.Dropdown.update(choices=Categories.list_categories(), value=category)
  
  @classmethod
  def select_category(cls, category):
    cls.category = category
    return cls.load_styles() 
  
  @classmethod
  def merge_category_files(cls):
    styles_to_save = [row for row in cls.load_style_file().to_numpy() if "::" not in row[1]]
    for category in Categories.list_categories(exclude_all=True):
      prefix = category + "::"
      for row in cls.load_style_file(category).to_numpy():
        row[1] = prefix + row[1]
        styles_to_save.append(row)
    cls.save_styles(pd.DataFrame(styles_to_save, columns=cls.full_cols), category=Categories.everything_category)
  
  @staticmethod
  def add_entry(array:np.ndarray, row, prefix:str):
    row[1] = row[1][len(prefix):]
    for i in range(len(array)):
      if array[i][1] == row[1]:
        array[i] = row
        return array
    return np.vstack([array,row])

  @classmethod
  def extract_category_files(cls):
    cls.categories_extracted = False
    prefixed_styles = [row for row in cls.load_style_file().to_numpy() if "::" in row[1]]
    for category in Categories.list_categories([p[1][:p[1].find('::')] for p in prefixed_styles], exclude_all=True):
      prefix = category + "::"
      additional_file_contents = cls.load_style_file(category).to_numpy()
      for prefixed_style in prefixed_styles:
        if prefixed_style[1].startswith(prefix):
          additional_file_contents = cls.add_entry(additional_file_contents, prefixed_style, prefix)
      cls.save_styles(pd.DataFrame(additional_file_contents, columns=cls.full_cols), category=category)
    cls.categories_extracted = True
  
  @classmethod
  def on_ui_tabs(cls):
    with gr.Blocks(analytics_enabled=False) as style_editor:
      dummy_component = gr.Label(visible=False)
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
            with gr.Column(scale=1, min_width=100):
              cls.view_categories_button = gr.Checkbox(value=False, label="View by category")
            with gr.Column(scale=10, min_width=100):
              gr.Markdown(value=cls.help_text)
          with gr.Group(visible=False) as cls.category_display:
            with gr.Row():
              with gr.Column(scale=1, min_width=400):
                cls.category_selection = gr.Dropdown(choices=Categories.list_categories(), value=Categories.everything_category, label="Category")
                cls.create_additional_category = gr.Button(value="Create new category")
              with gr.Column(scale=10):
                pass
      with gr.Row():
        with gr.Column(scale=1, min_width=150):
          cls.autosort_checkbox = gr.Checkbox(value=False, label="Autosort")
        with gr.Column(scale=1, min_width=250):
          cls.fix_sort_column_button = gr.Button(value="Renumber sort columm")
        with gr.Column(scale=10):
          pass
      with gr.Row():
        cls.dataeditor = gr.Dataframe(value=cls.load_style_file(), col_count=(len(cls.cols)+1,'fixed'), 
                                          wrap=True, max_rows=1000, show_label=True, interactive=True, elem_id="style_editor_grid")
 
      cls.search_and_replace_button.click(fn=cls.search_and_replace, inputs=[cls.search_box, cls.replace_box, cls.dataeditor], outputs=cls.dataeditor)

      cls.filter_box.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")
      cls.filter_select.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")

      cls.dataeditor.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")

      cls.dataeditor.input(fn=cls.save_styles, inputs=[cls.dataeditor, cls.autosort_checkbox], outputs=cls.dataeditor)
      cls.autosort_checkbox.change(fn=cls.save_styles, inputs=[cls.dataeditor, cls.autosort_checkbox], outputs=cls.dataeditor)
      cls.fix_sort_column_button.click(fn=cls.load_styles, outputs=cls.dataeditor)

      style_editor.load(fn=None, _js="when_loaded")

      cls.view_categories_button.change(fn=cls.view_by_category_changed, inputs=[cls.view_categories_button, cls.category_selection], outputs=[cls.category_display, cls.category_selection, cls.dataeditor])
      cls.create_additional_category.click(fn=cls.create_category, inputs=dummy_component, outputs=cls.category_selection, _js="new_category_dialog")
      cls.category_selection.change(fn=cls.select_category, inputs=cls.category_selection, outputs=cls.dataeditor)

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

class Categories:
  basedir = scripts.basedir()
  everything_category = 'All Categories'
  try:
    _default_style_file_path = cmd_opts.styles_file 
  except:
    _default_style_file_path = getattr(opts, 'styles_dir', None)

  _additional_style_files_directory = os.path.join(basedir,"additonal_style_files")
  if not os.path.exists(_additional_style_files_directory):
    os.mkdir(_additional_style_files_directory)
  _categories = [everything_category]
  for f in os.listdir(_additional_style_files_directory):
    if f.endswith(".csv"):
      _categories.append(os.path.split(f)[1][:-4])

  @classmethod
  def add_category(cls, category):
    if category and category not in cls._categories:
      cls._categories.append(category)

  @classmethod
  def list_categories(cls, categories_list=None, exclude_all=False):
    if categories_list:
      for category in categories_list:
        if category not in cls._categories:
          cls._categories.append(category)
    return cls._categories[(1 if exclude_all else 0):]
  
  @classmethod
  def filename_to_use(cls, category=None):
    return os.path.join(cls._additional_style_files_directory, f"{category}.csv") if (category and category!=cls.everything_category) else cls._default_style_file_path

script_callbacks.on_ui_tabs(StyleEditor.on_ui_tabs)
script_callbacks.on_app_started(StyleEditor.on_app_started)

