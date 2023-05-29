import gradio as gr
import modules.scripts as scripts
from modules import script_callbacks
from modules.shared import prompt_styles
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

  @classmethod
  def load_styles(cls):
    # bad lines are probably ones that had no 'notes', so append a ''
    # skip the first line (which has headers) and use our own
    cls.dataframe = pd.read_csv("styles.csv", header=None, names=cls.cols, on_bad_lines=lambda x : x.append(''), engine='python', skiprows=[0])
    return cls.dataframe

  @classmethod
  def save_styles(cls, data_to_save:pd.DataFrame):
    if cls.dataframe is None:
      return
    dts = data_to_save.drop(index=[i for (i, row) in data_to_save.iterrows() if row[0]==''])
    dts.to_csv("styles.csv", columns=cls.cols, index=False)
    #prompt_styles.reload()

  @classmethod
  def on_ui_tabs(cls):
    with gr.Blocks(analytics_enabled=False) as style_editor:
      with gr.Row():
        load = gr.Button(value="Reload Styles", elem_id="style_editor_load")
        save = gr.Button(value="Save Styles", elem_id="style_editor_save")
      with gr.Row():
        cls.dataeditor = gr.Dataframe(value=cls.load_styles, label="Styles", 
                                      col_count=(len(StyleEditor.cols),'fixed'), 
                                      wrap=True, max_rows=10,
                                      show_label=False, interactive=True, 
                                      elem_id="style_editor_grid")

      load.click(fn=StyleEditor.load_styles, outputs=cls.dataeditor)
      save.click(fn=StyleEditor.save_styles, inputs=cls.dataeditor, _js="refresh_style_list")

    return [(style_editor, "Style Editor", "style_editor")]

script_callbacks.on_ui_tabs(StyleEditor.on_ui_tabs)