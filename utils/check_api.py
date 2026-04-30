import requests
import sys
import os

API_KEY = ""
secrets_path = os.path.join(".streamlit", "secrets.toml")
if os.path.exists(secrets_path):
    with open(secrets_path) as f:
        for line in f:
            if "API_FOOTBALL_KEY" in line and "=" in line:
                API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

if not API_KEY:
    print("No se encontro API_FOOTBALL_KEY")
    sys.exit(1)

print("Key encontrada: " + API_KEY[:4] + "..." + API_KEY[-4:])

BASE = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
LEAGUE = 1
SEASON = 2026

print("=" * 60)
print("  VERIFICADOR - API Football - Mundial 2026")
print("=" * 60)

print("\n1. Estado de la cuenta...")
try:
    r = requests.get(BASE + "/status", headers=HEADERS, timeout=10)
    data = r.json()
    resp = data.get("response", {})
    if isinstance(resp, dict):
        subs = resp.get("subscription", {})
        req_info = resp.get("requests", {})
        print("   Plan: " + str(subs.get("plan", "?")))
        print("   Requests: " + str(req_info.get("current", "?")) + " / " + str(req_info.get("limit_day", "?")))
    else:
        print("   Respuesta inesperada: " + str(resp))
except Exception as e:
    print("   Error: " + str(e))

print("\n2. Liga Mundial 2026 disponible?")
try:
    r = requests.get(BASE + "/leagues", headers=HEADERS, params={"id": LEAGUE, "season": SEASON}, timeout=10)
    data = r.json()
    errors = data.get("errors", {})
    if errors:
        print("   NO - " + str(errors))
    elif data.get("results", 0) > 0:
        league = data["response"][0]["league"]
        print("   SI - " + league["name"])
    else:
        print("   NO - Liga no disponible para 2026")
except Exception as e:
    print("   Error: " + str(e))

print("\n3. Partidos cargados?")
try:
    r = requests.get(BASE + "/fixtures", headers=HEADERS, params={"league": LEAGUE, "season": SEASON}, timeout=15)
    data = r.json()
    errors = data.get("errors", {})
    if errors:
        print("   Error API: " + str(errors))
    elif data.get("results", 0) > 0:
        fixtures = data["response"]
        estados = {}
        for f in fixtures:
            st = f["fixture"]["status"]["short"]
            estados[st] = estados.get(st, 0) + 1
        ft = estados.get("FT", 0)
        ns = estados.get("NS", 0)
        print("   SI - " + str(len(fixtures)) + " partidos")
        print("   Estados: " + str(estados))
        print("   Finalizados: " + str(ft) + " | Por jugar: " + str(ns))
        if ft > 0:
            print("\n   >>> HAY RESULTADOS REALES! <<<")
        else:
            print("\n   Programados pero sin resultados aun")
    else:
        print("   NO - Sin partidos cargados")
except Exception as e:
    print("   Error: " + str(e))

print("\n4. Standings?")
try:
    r = requests.get(BASE + "/standings", headers=HEADERS, params={"league": LEAGUE, "season": SEASON}, timeout=10)
    data = r.json()
    errors = data.get("errors", {})
    if errors:
        print("   Error API: " + str(errors))
    elif data.get("results", 0) > 0:
        grupos = data["response"][0]["league"]["standings"]
        print("   SI - " + str(len(grupos)) + " grupos")
    else:
        print("   NO - Sin standings aun")
except Exception as e:
    print("   Error: " + str(e))

print("\n" + "=" * 60)
print("FT = datos reales | Sin fixtures = seguimos con simulacion")
print("=" * 60)
