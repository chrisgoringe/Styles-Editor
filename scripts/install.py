import launch

if not launch.is_installed("gradio>=3.30.0"):
    launch.run_pip("install gradio>=3.30.0", "requirement for Styles Editor")