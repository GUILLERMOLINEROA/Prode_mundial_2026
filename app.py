import runpy
from utils.group_config import group_config

config = group_config()
modo = str(config.get("modo_app", "previa")).strip().lower()

if modo == "mundial":
    runpy.run_path("views/mundial.py", run_name="__main__")
else:
    runpy.run_path("views/previa.py", run_name="__main__")
