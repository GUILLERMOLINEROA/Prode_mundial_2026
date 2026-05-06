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
