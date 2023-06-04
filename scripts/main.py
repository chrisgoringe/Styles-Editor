import gradio as gr
import modules.scripts as scripts
from modules import script_callbacks
from modules.shared import cmd_opts, opts
import pandas as pd
import numpy as np

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
  cols = ['name','prompt','negative_prompt', 'notes']
  dataframe:pd.DataFrame = None
  dataeditor = None
  as_last_saved:np.ndarray = None
  save_enabled = False
  try:
    style_file_path = cmd_opts.styles_file  #Automatic1111
  except:
    style_file_path = getattr(opts, 'styles_dir', None)

  @classmethod
  def load_styles(cls):
    # bad lines are probably ones that had no 'notes', so append a ''
    # skip the first line (which has headers) and use our own
    try:
      cls.dataframe = pd.read_csv(cls.style_file_path, header=None, names=cls.cols, on_bad_lines=lambda x : x.append(''), engine='python', skiprows=[0])
    except:
      cls.dataframe = pd.DataFrame(columns=cls.cols)
    if cls.dataframe.shape[1]==4:
      cls.dataframe.insert(loc=0, column="index", value=[i for i in range(1,cls.dataframe.shape[0]+1)])
    cls.dataframe.fillna('', inplace=True)
    cls.as_last_saved = cls.dataframe.to_numpy(copy=True)
    return cls.dataframe

  @classmethod
  def save_styles(cls, data_to_save:pd.DataFrame):
    dts = data_to_save.drop(index=[i for (i, row) in data_to_save.iterrows() if row[1]==''])
    dts.to_csv(cls.style_file_path, columns=cls.cols, index=False)
    cls.as_last_saved = cls.dataframe.to_numpy(copy=True)
    cls.save_enabled = False
    return gr.Button.update(interactive=cls.save_enabled)
  
  @classmethod
  def maybe_enable_save(cls, current_data:pd.DataFrame):
    if not cls.save_enabled:
      try:
        current_data.fillna('', inplace=True)
        cdnp = current_data.to_numpy()
        equal = np.array_equal(cdnp, cls.as_last_saved)
        cls.save_enabled = not equal
      except:
        cls.save_enabled = True
    return gr.Button.update(interactive=cls.save_enabled)

  @classmethod
  def on_ui_tabs(cls):
    with gr.Blocks(analytics_enabled=False) as style_editor:
      with gr.Row(equal_height=True):
        with gr.Column(scale=1, min_width=100):
          cls.load_button = gr.Button(value="Reload Styles", elem_id="style_editor_load")
          cls.save_button = gr.Button(value="Save Styles", elem_id="style_editor_save", interactive=False)
      #with gr.Row(equal_height=True):
        with gr.Column(scale=3, min_width=100):
          cls.filter_box = gr.Textbox(max_lines=1, interactive=True, placeholder="filter", elem_id="style_editor_filter", show_label=False)
          cls.filter_select = gr.Dropdown(choices=["Exact match", "Case insensitive", "regex"], value="Exact match", show_label=False)
      with gr.Row():
        cls.dataeditor = gr.Dataframe(value=cls.load_styles, label="Styles", 
                                      col_count=(len(cls.cols)+1,'fixed'), 
                                      wrap=True, max_rows=1000,
                                      show_label=False, interactive=True, 
                                      elem_id="style_editor_grid")

      cls.load_button.click(fn=cls.load_styles, outputs=cls.dataeditor)
      cls.save_button.click(fn=cls.save_styles, inputs=cls.dataeditor, outputs=cls.save_button, _js="refresh_style_list")
      cls.filter_box.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")
      cls.filter_select.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")
      cls.dataeditor.change(fn=None, inputs=[cls.filter_box, cls.filter_select], _js="filter_style_list")
      cls.dataeditor.change(fn=cls.maybe_enable_save, inputs=cls.dataeditor, outputs=cls.save_button)

    return [(style_editor, "Style Editor", "style_editor")]

script_callbacks.on_ui_tabs(StyleEditor.on_ui_tabs)