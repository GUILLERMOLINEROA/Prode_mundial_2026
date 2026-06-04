import os
import runpy
os.environ["GROUP_ID"] = "pelle"
runpy.run_path("app.py", run_name="__main__")
