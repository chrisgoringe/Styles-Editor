import gradio as gr
import modules.scripts as scripts
from modules import script_callbacks

import pandas as pd
import os

from scripts.filemanager import FileManager
from scripts.additionals import Additionals
from scripts.background import Background
from scripts.shared import display_columns

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
- Create new additional style file moved to the dropdown
- Merge into master now automatic when you uncheck the `Edit additional` box

## Changed in recent updates:
- Delete from master list removes from additional style file as well
- Option to encrypt backups
- Restored the `notes` column
- Automatically create new Additional Style Files if needed
- Automatically delete empty Additional Style Files on merge

"""
  backup = Background(FileManager.do_backup, 600)

  @staticmethod
  def _to_numeric(series:pd.Series):
    nums = pd.to_numeric(series)
    if any(nums.isna()):
      raise Exception("don't update display")
    return nums
  
  @classmethod
  def _sort_dataset(cls, data:pd.DataFrame) -> pd.DataFrame:
      try:
        return data.sort_values(by='sort', axis='index', inplace=False, na_position='first', key=cls._to_numeric)
      except:
        return data
  
  @classmethod
  def _drop_deleted(cls, data:pd.DataFrame) -> pd.DataFrame:
    rows_to_drop = [i for (i, row) in data.iterrows() if row[0]=='!!!']
    for style in [row[1] for (_, row) in data.iterrows() if row[0]=='!!!']:
      FileManager.remove_from_additional(style)
    return data.drop(index=rows_to_drop)
      
  @classmethod
  def handle_autosort_checkbox_change(cls, data:pd.DataFrame, autosort) -> pd.DataFrame:
    if autosort:
      data = cls._sort_dataset(data)
      FileManager.save_styles(data)
    return data

  @classmethod
  def handle_dataeditor_input(cls, data:pd.DataFrame, autosort) -> pd.DataFrame:
    cls.backup.set_pending()
    data = cls._drop_deleted(data)
    data = cls._sort_dataset(data) if autosort else data
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
    return pd.DataFrame(data=data_np, columns=display_columns)
  
  @classmethod
  def handle_use_additional_styles_box_change(cls, activate, filename):
    FileManager.current_styles_file_path = Additionals.full_path(filename) if activate else FileManager.default_style_file_path
    if activate:
      FileManager.update_additional_style_files()
      labels = Additionals.additional_style_files(display_names=True, include_new=True)
      selected = Additionals.display_name(FileManager.current_styles_file_path)
      selected = selected if selected in labels else labels[0] if len(labels)>0 else ''
      return gr.Row.update(visible=activate), FileManager.load_styles(), gr.Dropdown.update(choices=labels, value=selected)
    else:
      FileManager.merge_additional_style_files()
      return gr.Row.update(visible=activate), FileManager.load_styles(), gr.Dropdown.update()
  
  @classmethod
  def handle_style_file_selection_change(cls, prefix, _):
    if prefix:
      FileManager.create_file_if_missing(prefix)
      FileManager.current_styles_file_path = Additionals.full_path(prefix)
    else:
      prefix = Additionals.display_name(FileManager.current_styles_file_path)
    return FileManager.load_styles(), gr.Dropdown.update(choices=Additionals.additional_style_files(display_names=True, include_new=True), value=prefix)
  
  @classmethod
  def handle_use_encryption_checkbox_changed(cls, encrypt):
    FileManager.encrypt = encrypt

  @classmethod
  def handle_encryption_key_change(cls, key):
    FileManager.encrypt_key = key

  @classmethod
  def handle_restore_backup_file_upload(cls, tempfile):
    error = FileManager.restore_from_backup(tempfile.name)
    if error is None:
      FileManager.update_additional_style_files()
      return gr.Text.update(visible=True, value="Styles restored"), False, FileManager.load_styles(use_default=True)
    else:
      return gr.Text.update(visible=True, value=error), False, FileManager.load_styles(use_default=True)
    
  @classmethod
  def handle_restore_backup_file_clear(cls):
    return gr.Text.update(visible=False)

  @classmethod
  def on_ui_tabs(cls):
    with gr.Blocks(analytics_enabled=False) as style_editor:
      dummy_component = gr.Label(visible=False)
      with gr.Row():
        with gr.Column(scale=1, min_width=400):
          with gr.Accordion(label="Documentation and Recent Changes", open=False):
            gr.HTML(value="<a href='https://github.com/chrisgoringe/Styles-Editor/blob/main/readme.md' target='_blank'>Link to Documentation</a>")
            gr.Markdown(value=cls.update_help)
            gr.HTML(value="<a href='https://github.com/chrisgoringe/Styles-Editor/blob/main/changes.md' target='_blank'>Change log</a>")
        with gr.Column(scale=1, min_width=400):
          with gr.Accordion(label="Encryption", open=False):
            cls.use_encryption_checkbox = gr.Checkbox(value=False, label="Use Encryption")
            cls.encryption_key_textbox = gr.Textbox(max_lines=1, placeholder="encryption key", label="Encryption Key")
            gr.Markdown(value="If checked, and a key is provided, backups are encrypted. The active style file and additional style files are not.")
            gr.Markdown(value="Files are encrypted using pyAesCrypt (https://pypi.org/project/pyAesCrypt/)")
        with gr.Column(scale=1, min_width=400):
          with gr.Accordion(label="Restore from Backup", open=False):
            gr.Markdown(value="If restoring from an encrypted backup, enter the encrption key under `Encryption` first.")
            cls.restore_backup_file_upload = gr.File(file_types=[".csv", ".aes"], label="Restore from backup")
            cls.restore_result = gr.Text(visible=False, label="Result:")
        with gr.Column(scale=1, min_width=400):
          with gr.Accordion(label="Filter view", open=False):
            cls.filter_textbox = gr.Textbox(max_lines=1, interactive=True, placeholder="filter", elem_id="style_editor_filter", show_label=False)
            cls.filter_select = gr.Dropdown(choices=["Exact match", "Case insensitive", "regex"], value="Exact match", show_label=False)
        with gr.Column(scale=1, min_width=400):
          with gr.Accordion(label="Search and replace", open=False):
            cls.search_box = gr.Textbox(max_lines=1, interactive=True, placeholder="search for", show_label=False)
            cls.replace_box= gr.Textbox(max_lines=1, interactive=True, placeholder="replace with", show_label=False)
            cls.search_and_replace_button = gr.Button(value="Search and Replace")
        with gr.Column(scale=1, min_width=400):
          pass
      with gr.Row():
        with gr.Column():
          with gr.Row():
            cls.use_additional_styles_checkbox = gr.Checkbox(value=False, label="Edit additional style files")
          with gr.Group(visible=False) as cls.additional_file_display:
            with gr.Row():
              with gr.Column(scale=1, min_width=400):
                cls.style_file_selection = gr.Dropdown(choices=Additionals.additional_style_files(display_names=True, include_new=True), value=Additionals.display_name(''), 
                                                      label="Additional Style File", scale=1, min_width=200)
              with gr.Column(scale=4):
                pass
      with gr.Row():
        with gr.Column(scale=1, min_width=150):
          cls.autosort_checkbox = gr.Checkbox(value=False, label="Autosort")
        with gr.Column(scale=10):
          pass
      with gr.Row():
        cls.dataeditor = gr.Dataframe(value=FileManager.load_styles(), col_count=(len(display_columns),'fixed'), 
                                          wrap=True, max_rows=1000, show_label=False, interactive=True, elem_id="style_editor_grid")
      
      cls.search_and_replace_button.click(fn=cls.handle_search_and_replace_click, inputs=[cls.search_box, cls.replace_box, cls.dataeditor], outputs=cls.dataeditor)

      cls.filter_textbox.change(fn=None, inputs=[cls.filter_textbox, cls.filter_select], _js="filter_style_list")
      cls.filter_select.change(fn=None, inputs=[cls.filter_textbox, cls.filter_select], _js="filter_style_list")

      cls.use_encryption_checkbox.change(fn=cls.handle_use_encryption_checkbox_changed, inputs=[cls.use_encryption_checkbox], outputs=[])
      cls.encryption_key_textbox.change(fn=cls.handle_encryption_key_change, inputs=[cls.encryption_key_textbox], outputs=[])
      cls.restore_backup_file_upload.upload(fn=cls.handle_restore_backup_file_upload, inputs=[cls.restore_backup_file_upload], outputs=[cls.restore_result, cls.use_additional_styles_checkbox, cls.dataeditor])
      cls.restore_backup_file_upload.clear(fn=cls.handle_restore_backup_file_clear, inputs=[], outputs=[cls.restore_result])

      cls.dataeditor.change(fn=None, inputs=[cls.filter_textbox, cls.filter_select], _js="filter_style_list")

      cls.dataeditor.input(fn=cls.handle_dataeditor_input, inputs=[cls.dataeditor, cls.autosort_checkbox], outputs=cls.dataeditor)
      cls.autosort_checkbox.change(fn=cls.handle_autosort_checkbox_change, inputs=[cls.dataeditor, cls.autosort_checkbox], outputs=cls.dataeditor)

      style_editor.load(fn=None, _js="when_loaded")
      style_editor.load(fn=cls.backup.start, inputs=[], outputs=[])

      cls.use_additional_styles_checkbox.change(fn=cls.handle_use_additional_styles_box_change, inputs=[cls.use_additional_styles_checkbox, cls.style_file_selection], 
                                                outputs=[cls.additional_file_display, cls.dataeditor, cls.style_file_selection])
      cls.style_file_selection.change(fn=cls.handle_style_file_selection_change, inputs=[cls.style_file_selection, dummy_component], 
                                      outputs=[cls.dataeditor,cls.style_file_selection], _js="style_file_selection_change")


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