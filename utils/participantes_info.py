import os
import pandas as pd
from utils.group_config import participantes_info_path


def cargar_participantes_info():
    """
    Carga participantes_info.csv del grupo activo y devuelve:
    {
        "CODIGO": {
            "nombre": "...",
            "email": "...",
            "nacionalidad": "..."
        }
    }
    """
    path = participantes_info_path()
    if not os.path.exists(path):
        return {}

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    out = {}
    for _, row in df.iterrows():
        codigo = str(row.get("codigo", "")).strip().upper()
        if not codigo:
            continue

        out[codigo] = {
            "nombre": str(row.get("nombre", "")).strip(),
            "email": str(row.get("email", "")).strip(),
            "nacionalidad": str(row.get("nacionalidad", "")).strip(),
        }

    return out
