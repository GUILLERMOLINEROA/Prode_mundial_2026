import os

try:
    import streamlit as st
except Exception:
    st = None


DEFAULT_GROUP_ID = "oficina"


def get_group_id():
    """
    Obtiene el grupo activo.
    Prioridad:
    1. Variable de entorno GROUP_ID
    2. st.secrets["GROUP_ID"] si existe
    3. oficina por default
    """
    env_group = os.environ.get("GROUP_ID")
    if env_group:
        return env_group.strip()

    if st is not None:
        try:
            secret_group = st.secrets.get("GROUP_ID", "")
            if secret_group:
                return secret_group.strip()
        except Exception:
            pass

    return DEFAULT_GROUP_ID


def group_base_path(group_id=None):
    group_id = group_id or get_group_id()
    return os.path.join("data", "groups", group_id)


def group_file(filename, group_id=None):
    return os.path.join(group_base_path(group_id), filename)


def entregas_path(group_id=None):
    return group_file("entregas.csv", group_id)


def participantes_info_path(group_id=None):
    return group_file("participantes_info.csv", group_id)


def overrides_path(group_id=None):
    return group_file("overrides.json", group_id)


def participantes_dir(group_id=None):
    return os.path.join(group_base_path(group_id), "participantes")


def fotos_dir(group_id=None):
    return os.path.join(group_base_path(group_id), "fotos")


def group_exists(group_id=None):
    return os.path.exists(group_base_path(group_id))


def group_config():
    """Lee el config.json del grupo activo."""
    import json
    path = group_file("config.json")
    defaults = {
        "nombre_display": "PRODE Mundialista 2026",
        "tono": "picante",
        "prompt_gemini": "Sos un analista de fútbol argentino, sarcástico y con humor. Máximo 3 oraciones.",
        "banners_propios": False,
    }
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
                defaults.update(config)
            except Exception:
                pass
    return defaults


def banners_dir():
    """Retorna la carpeta de banners del grupo si tiene propios, sino la global."""
    config = group_config()
    if config.get("banners_propios"):
        group_banners = os.path.join(group_base_path(), "banners")
        if os.path.exists(group_banners) and os.listdir(group_banners):
            return group_banners
    return os.path.join("assets", "banners")
