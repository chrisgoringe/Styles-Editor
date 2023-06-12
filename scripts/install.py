import launch
from packaging import version
import gradio

if version.parse(gradio.__version__) < version.parse("3.30.0"):
    launch.run_pip("install gradio==3.30.0", "requirements for Styles Editor")