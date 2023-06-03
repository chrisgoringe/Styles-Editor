import gradio as gr
import modules.scripts as scripts
from modules import script_callbacks
from modules.shared import opts
import pandas as pd

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
  dataframe = None
  dataeditor = None
  styles_filename = getattr(opts, 'styles_dir', None)

  @classmethod
  def load_styles(cls):
    # bad lines are probably ones that had no 'notes', so append a ''
    # skip the first line (which has headers) and use our own
    try:
      cls.dataframe = pd.read_csv(cls.styles_filename, header=None, names=cls.cols, on_bad_lines=lambda x : x.append(''), engine='python', skiprows=[0])
    except:
      cls.dataframe = pd.DataFrame(columns=cls.cols)
    if cls.dataframe.shape[1]==4:
      cls.dataframe.insert(loc=0, column="index", value=[i for i in range(1,cls.dataframe.shape[0]+1)])
    return cls.dataframe

  @classmethod
  def save_styles(cls, data_to_save:pd.DataFrame):
    if cls.dataframe is None:
      return
    dts = data_to_save.drop(index=[i for (i, row) in data_to_save.iterrows() if row[1]==''])
    dts.to_csv(cls.styles_filename, columns=cls.cols, index=False)
    return gr.Button.update(interactive=False)
  
  @classmethod
  def enable_save(cls):
    return gr.Button.update(interactive=True)

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
      cls.dataeditor.change(fn=cls.enable_save, outputs=cls.save_button)

    return [(style_editor, "Style Editor", "style_editor")]

script_callbacks.on_ui_tabs(StyleEditor.on_ui_tabs)