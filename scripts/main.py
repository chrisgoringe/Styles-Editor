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
    try:
      cls.dataframe = pd.read_csv("styles.csv", header=None, names=cls.cols, on_bad_lines=lambda x : x.append(''), engine='python', skiprows=[0])
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
    dts.to_csv("styles.csv", columns=cls.cols, index=False)

  @classmethod
  def on_ui_tabs(cls):
    with gr.Blocks(analytics_enabled=False) as style_editor:
      with gr.Row():
        cls.load_button = gr.Button(value="Reload Styles", elem_id="style_editor_load")
        cls.save_button = gr.Button(value="Save Styles", elem_id="style_editor_save")
      with gr.Row():
        cls.filter_box = gr.Textbox(max_lines=1, interactive=True, placeholder="filter", elem_id="style_editor_filter", show_label=False)
      with gr.Row():
        cls.dataeditor = gr.Dataframe(value=cls.load_styles, label="Styles", 
                                      col_count=(len(StyleEditor.cols)+1,'fixed'), 
                                      wrap=True, max_rows=1000,
                                      show_label=False, interactive=True, 
                                      elem_id="style_editor_grid")

      cls.load_button.click(fn=StyleEditor.load_styles, outputs=cls.dataeditor)
      cls.save_button.click(fn=StyleEditor.save_styles, inputs=cls.dataeditor, _js="refresh_style_list")
      cls.filter_box.change(fn=None, _js="filter_style_list")

    return [(style_editor, "Style Editor", "style_editor")]

script_callbacks.on_ui_tabs(StyleEditor.on_ui_tabs)