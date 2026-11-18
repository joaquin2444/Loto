import json
import os
import urllib.request
from datetime import date, timedelta

JUEGOS = {
    "primitiva": "LAPR",
    "bonoloto": "BONO",
    "euromillones": "EMIL",
    "gordo": "ELGR",
}

BASE = "https://www.loteriasyapuestas.es/servicios/buscadorSorteos"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.loteriasyapuestas.es/es/resultados",
}

hoy = date.today()
inicio = hoy - timedelta(days=30)

os.makedirs("data", exist_ok=True)

salida = {"actualizado": hoy.isoformat(), "juegos": {}}

for nombre, codigo in JUEGOS.items():
    url = (
        BASE
        + "?game_id=" + codigo
        + "&celebrados=true"
        + "&fechaInicioInclusiva=" + inicio.strftime("%Y%m%d")
        + "&fechaFinInclusiva=" + hoy.strftime("%Y%m%d")
    )
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            datos = json.loads(r.read().decode("utf-8", "replace"))
        salida["juegos"][nombre] = datos
        print(nombre, "OK", len(datos), "sorteos")
    except Exception as e:
        print(nombre, "ERROR", e)
        salida["juegos"][nombre] = {"error": str(e)}

with open("data/resultados.json", "w", encoding="utf-8") as f:
    json.dump(salida, f, ensure_ascii=False, indent=2)

print("Guardado data/resultados.json")
