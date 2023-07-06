import gradio as gr
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Tuple
import modules.scripts as scripts
from modules import script_callbacks

import pandas as pd
import threading

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

class ParameterString(BaseModel):
  value: str

class ParameterBool(BaseModel):
  value: bool

class StyleEditor:
  update_help = """# Recent changes:
## Changed in this update:
- Automatically merge styles when changing away from this tab

## Changed in recent updates:
- Select row(s) then press `M` to move them
- Ctrl-right-click to select multiple rows
- Create new additional style file moved to the dropdown
- Merge into master now automatic when you uncheck the `Edit additional` box
- Moved `Use additional` and `Autosort` checkboxes into `Advanced`

"""
  backup = Background(FileManager.do_backup, 600)
  api_calls_outstanding = []
  api_lock = threading.Lock()
  this_tab_selected = False

  @classmethod
  def handle_this_tab_selected(cls):
    FileManager.clear_style_cache()
    cls.this_tab_selected = True
    return FileManager.get_current_styles()

  @classmethod
  def handle_another_tab_selected(cls):
    if cls.this_tab_selected:
      FileManager.merge_additional_style_files()
      FileManager.clear_style_cache()
    cls.this_tab_selected = False

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
  def handle_autosort_checkbox_change(cls, data:pd.DataFrame, autosort) -> pd.DataFrame:
    if autosort:
      data = cls._sort_dataset(data)
      FileManager.save_current_styles(data)
    return data

  @classmethod
  def handle_dataeditor_input(cls, data:pd.DataFrame, autosort) -> pd.DataFrame:
    cls.backup.set_pending()
    data = cls._sort_dataset(data) if autosort else data
    FileManager.save_current_styles(data)
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
      return gr.Row.update(visible=activate), FileManager.get_current_styles(), gr.Dropdown.update(choices=labels, value=selected)
    else:
      FileManager.merge_additional_style_files()
      return gr.Row.update(visible=activate), FileManager.get_current_styles(), gr.Dropdown.update()
  
  @classmethod
  def handle_style_file_selection_change(cls, prefix, _):
    if prefix:
      FileManager.create_file_if_missing(prefix)
      FileManager.current_styles_file_path = Additionals.full_path(prefix)
    else:
      prefix = Additionals.display_name(FileManager.current_styles_file_path)
    return FileManager.get_current_styles(), gr.Dropdown.update(choices=Additionals.additional_style_files(display_names=True, include_new=True), value=prefix)
  
  @classmethod
  def handle_use_encryption_checkbox_changed(cls, encrypt):
    FileManager.encrypt = encrypt
    return ""

  @classmethod
  def handle_encryption_key_change(cls, key):
    FileManager.encrypt_key = key

  @classmethod
  def handle_restore_backup_file_upload(cls, tempfile):
    error = FileManager.restore_from_backup(tempfile.name)
    if error is None:
      FileManager.update_additional_style_files()
      return gr.Text.update(visible=True, value="Styles restored"), False, FileManager.get_styles()
    else:
      return gr.Text.update(visible=True, value=error), False, FileManager.get_styles()
    
  @classmethod
  def handle_restore_backup_file_clear(cls):
    return gr.Text.update(visible=False)
  
  @classmethod
  def handle_outstanding_api_calls(cls):
    with cls.api_lock:
      for command, value in cls.api_calls_outstanding:
        match command:
          case "delete":
            FileManager.remove_style(maybe_prefixed_style=value)
          case "move":
            FileManager.move_to_additional(maybe_prefixed_style=value[0], new_prefix=value[1])
      cls.api_calls_outstanding = []
    return FileManager.get_current_styles()

  @classmethod
  def on_ui_tabs(cls):
    with gr.Blocks(analytics_enabled=False) as style_editor:
      dummy_component = gr.Label(visible=False)
      with gr.Row():
        cls.do_api = gr.Button(visible=False, elem_id="style_editor_handle_api")
        with gr.Column(scale=1, min_width=400):
          with gr.Accordion(label="Documentation and Recent Changes", open=False):
            gr.HTML(value="<a href='https://github.com/chrisgoringe/Styles-Editor/blob/main/readme.md' target='_blank'>Link to Documentation</a>")
            gr.Markdown(value=cls.update_help)
            gr.HTML(value="<a href='https://github.com/chrisgoringe/Styles-Editor/blob/main/changes.md' target='_blank'>Change log</a>")
        with gr.Column(scale=1, min_width=400):
          with gr.Accordion(label="Encryption", open=False, elem_id="style_editor_encryption_accordian"):
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
          with gr.Accordion(label="Filter view", open=False, elem_id="style_editor_filter_accordian"):
            cls.filter_textbox = gr.Textbox(max_lines=1, interactive=True, placeholder="filter", elem_id="style_editor_filter", show_label=False)
            cls.filter_select = gr.Dropdown(choices=["Exact match", "Case insensitive", "regex"], value="Exact match", show_label=False)
        with gr.Column(scale=1, min_width=400):
          with gr.Accordion(label="Search and replace", open=False):
            cls.search_box = gr.Textbox(max_lines=1, interactive=True, placeholder="search for", show_label=False)
            cls.replace_box= gr.Textbox(max_lines=1, interactive=True, placeholder="replace with", show_label=False)
            cls.search_and_replace_button = gr.Button(value="Search and Replace")
        with gr.Column(scale=1, min_width=400):
          with gr.Accordion(label="Advanced options", open=False):
            cls.use_additional_styles_checkbox = gr.Checkbox(value=False, label="Edit additional style files")
            cls.autosort_checkbox = gr.Checkbox(value=False, label="Autosort")
            with gr.Group(visible=False) as cls.additional_file_display:
              cls.style_file_selection = gr.Dropdown(choices=Additionals.additional_style_files(display_names=True, include_new=True), 
                                                    value=Additionals.display_name(''), 
                                                    label="Additional Style File", scale=1, min_width=200)
      with gr.Row():
        cls.dataeditor = gr.Dataframe(value=FileManager.get_current_styles(), col_count=(len(display_columns),'fixed'), 
                                          wrap=True, max_rows=1000, show_label=False, interactive=True, elem_id="style_editor_grid")
      
      cls.search_and_replace_button.click(fn=cls.handle_search_and_replace_click, inputs=[cls.search_box, cls.replace_box, cls.dataeditor], outputs=cls.dataeditor)

      cls.filter_textbox.change(fn=None, inputs=[cls.filter_textbox, cls.filter_select], _js="filter_style_list")
      cls.filter_select.change(fn=None, inputs=[cls.filter_textbox, cls.filter_select], _js="filter_style_list")

      cls.use_encryption_checkbox.change(fn=cls.handle_use_encryption_checkbox_changed, inputs=[cls.use_encryption_checkbox], outputs=[dummy_component], _js="encryption_change")
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

      cls.do_api.click(fn=cls.handle_outstanding_api_calls,outputs=cls.dataeditor)

    return [(style_editor, "Style Editor", "style_editor")]

  @classmethod
  def on_app_started(cls, block:gr.Blocks, api:FastAPI):

    @api.post("/style-editor/delete-style/")
    def delete_style(stylename:ParameterString):
      with cls.api_lock:
        cls.api_calls_outstanding.append(("delete",stylename.value))

    @api.post("/style-editor/move-style/")
    def move_style(style:ParameterString, new_prefix:ParameterString):
      with cls.api_lock:
        cls.api_calls_outstanding.append(("move",(style.value, new_prefix.value)))

    @api.post("/style-editor/check-api/")
    def check() -> ParameterBool:
      return ParameterBool(value=True)
    
    @api.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
      exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
      content = {'status_code': 422, 'message': exc_str, 'data': None}
      return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    with block:
      for tabs in block.children:
        if isinstance(tabs, gr.layouts.Tabs):
          for tab in tabs.children:
            if isinstance(tab, gr.layouts.Tab):
              if tab.id=="style_editor":
                tab.select(fn=cls.handle_this_tab_selected, outputs=cls.dataeditor)
              else:
                tab.select(fn=cls.handle_another_tab_selected)
              if tab.id=="txt2img" or tab.id=="img2img":
                tab.select(fn=None, inputs=tab, _js="press_refresh_button")

script_callbacks.on_ui_tabs(StyleEditor.on_ui_tabs)
script_callbacks.on_app_started(StyleEditor.on_app_started)