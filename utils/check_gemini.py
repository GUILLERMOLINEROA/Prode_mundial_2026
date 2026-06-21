"""
utils/check_gemini.py
Diagnostico aislado de la API de Gemini (espejo de check_api.py pero para GEMINI_API_KEY).

Que hace:
- Lee GEMINI_API_KEY desde .streamlit/secrets.toml o desde la variable de entorno.
- Reporta que version del SDK esta instalada (google-generativeai y/o google-genai).
- Lista los modelos disponibles para esa key (para confirmar si "gemini-2.5-flash" existe).
- Hace una llamada real y simple a gemini-2.5-flash e imprime el resultado o el error COMPLETO
  (tipo de excepcion + mensaje), sin loguear la key entera (solo primeros/ultimos chars).

Uso:
    python utils/check_gemini.py
    python utils/check_gemini.py --modelo gemini-2.5-flash
"""
import os
import sys

MODELO = "gemini-2.5-flash"
for i, a in enumerate(sys.argv):
    if a == "--modelo" and i + 1 < len(sys.argv):
        MODELO = sys.argv[i + 1]


def leer_key():
    # 1. .streamlit/secrets.toml (mismo formato que usa check_api.py)
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        with open(secrets_path, encoding="utf-8") as f:
            for line in f:
                if "GEMINI_API_KEY" in line and "=" in line:
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    # 2. variable de entorno
    return os.environ.get("GEMINI_API_KEY", "")


KEY = leer_key()

print("=" * 60)
print("  VERIFICADOR - Gemini API - PRODE Mundial 2026")
print("=" * 60)

if not KEY:
    print("\nNo se encontro GEMINI_API_KEY (ni en .streamlit/secrets.toml ni en el entorno).")
    print("Defini la variable GEMINI_API_KEY o agregala al secrets.toml local y reintenta.")
    sys.exit(1)

if len(KEY) >= 8:
    print("\nKey encontrada: " + KEY[:4] + "..." + KEY[-4:] + "  (largo=" + str(len(KEY)) + ")")
else:
    print("\nKey encontrada pero es sospechosamente corta (largo=" + str(len(KEY)) + ")")

# -----------------------------------------------------------------------------
# 1. Que SDK hay instalado
# -----------------------------------------------------------------------------
print("\n1. SDK instalado")
try:
    import google.generativeai as genai
    ver = getattr(genai, "__version__", "?")
    print("   google-generativeai (legacy): instalado, version " + str(ver))
    tiene_legacy = True
except Exception as e:
    print("   google-generativeai (legacy): NO disponible -> " + type(e).__name__ + ": " + str(e))
    tiene_legacy = False

try:
    import google.genai  # noqa: F401
    print("   google-genai (nuevo SDK): instalado")
except Exception:
    print("   google-genai (nuevo SDK): no instalado")

if not tiene_legacy:
    print("\nEl codigo de la app usa 'import google.generativeai'. Si no esta instalado, eso es la causa.")
    print("Instalalo con: python -m pip install google-generativeai")
    sys.exit(1)

# -----------------------------------------------------------------------------
# 2. Listar modelos disponibles para esta key
# -----------------------------------------------------------------------------
print("\n2. Modelos disponibles para esta key (los que soportan generateContent)")
try:
    genai.configure(api_key=KEY)
    encontrados = []
    target_visible = False
    for m in genai.list_models():
        metodos = getattr(m, "supported_generation_methods", []) or []
        if "generateContent" in metodos:
            nombre = m.name  # ej "models/gemini-2.5-flash"
            encontrados.append(nombre)
            if MODELO in nombre:
                target_visible = True
    if encontrados:
        for n in encontrados:
            marca = "  <-- objetivo" if MODELO in n else ""
            print("   " + n + marca)
    else:
        print("   (la lista vino vacia)")
    print("\n   '" + MODELO + "' visible para esta key: " + ("SI" if target_visible else "NO"))
except Exception as e:
    print("   ERROR listando modelos -> " + type(e).__name__ + ": " + str(e))
    print("   (un 400/403 aca sugiere key invalida o no habilitada para la Generative Language API)")

# -----------------------------------------------------------------------------
# 3. Llamada real de prueba
# -----------------------------------------------------------------------------
print("\n3. Llamada real a " + MODELO)
try:
    model = genai.GenerativeModel(MODELO)
    response = model.generate_content("Decime en una sola frase corta por que River es mas grande que Boca.")
    print("   OK - respuesta recibida:")
    print("   " + (response.text or "").strip())
except Exception as e:
    print("   ERROR -> " + type(e).__name__ + ": " + str(e))
    msg = str(e)
    if "429" in msg or "quota" in msg.lower() or "exhausted" in msg.lower():
        print("   >>> Parece RATE LIMIT / CUOTA AGOTADA (429).")
    elif "404" in msg or "not found" in msg.lower():
        print("   >>> Modelo no encontrado: el id '" + MODELO + "' no es valido para esta key/SDK.")
    elif "permission" in msg.lower() or "403" in msg or "API_KEY_INVALID" in msg or "401" in msg:
        print("   >>> Key invalida / sin permisos.")

print("\n" + "=" * 60)
print("Listo. Si el paso 3 dio OK, Gemini funciona y el problema es de la app (cache/fallback).")
print("=" * 60)
