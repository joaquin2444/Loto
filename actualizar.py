import json
import os
import re
import urllib.request
from datetime import date, timedelta

WEBS = {
    "primitiva": "https://www.combinacionganadora.com/primitiva/",
    "bonoloto": "https://www.combinacionganadora.com/bonoloto/",
    "euromillones": "https://www.combinacionganadora.com/euromillones/",
}

DIAS_A_GUARDAR = 100  # un poco mas de 3 meses
RUTA = "data/historial.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "es-ES,es;q=0.9",
}

FECHA = re.compile(r"\d{1,2} de [a-záéíóúñ]+ de \d{4}", re.I)
FECHA_DIA = re.compile(
    r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo),? \d{1,2} [a-záéíóúñ]+ \d{4}",
    re.I,
)
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def limpiar(fragmento):
    texto = re.sub(r"<[^>]+>", " ", fragmento)
    return re.sub(r"\s+", " ", texto).strip()


def a_iso(texto):
    m = re.search(r"(\d{1,2})(?: de)? ([a-záéíóúñ]+)(?: de)? (\d{4})", (texto or "").lower())
    if not m or m.group(2) not in MESES:
        return None
    try:
        return date(int(m.group(3)), MESES[m.group(2)], int(m.group(1))).isoformat()
    except ValueError:
        return None


def extraer(nombre, html):
    html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)

    m = re.search(
        r'<ul[^>]*data-gametype="' + nombre + r'"[^>]*>(.*?)</ul>', html, flags=re.S
    )
    if not m:
        m = re.search(
            r'<ul[^>]*class="[^"]*numbers[^"]*"[^>]*>(.*?)</ul>', html, flags=re.S
        )
    if not m:
        return {"error": "no se encontro la lista de numeros"}

    numeros = []
    extras = []
    for attrs, contenido in re.findall(r"<li([^>]*)>(.*?)</li>", m.group(1), flags=re.S):
        valor = limpiar(contenido)
        if not valor:
            continue
        if "data-extra" in attrs:
            extras.append(valor)
        else:
            numeros.append(valor)

    antes = limpiar(html[max(0, m.start() - 3000): m.start()])
    con_dia = FECHA_DIA.findall(antes)
    if con_dia:
        fecha = con_dia[-1]
    else:
        fechas = FECHA.findall(antes)
        fecha = fechas[-1] if fechas else None

    despues = limpiar(html[m.end(): m.end() + 600])
    joker = re.search(r"Joker\s*(\d{7})", despues)

    return {
        "fecha": fecha,
        "iso": a_iso(fecha),
        "numeros": numeros,
        "extras": extras,
        "joker": joker.group(1) if joker else None,
    }


# Cargar el historial que ya existe
os.makedirs("data", exist_ok=True)
historial = {"actualizado": "", "juegos": {}}
if os.path.exists(RUTA):
    try:
        with open(RUTA, encoding="utf-8") as f:
            historial = json.load(f)
    except Exception as e:
        print("No se pudo leer el historial, se empieza de nuevo:", e)

hoy = date.today()
limite = (hoy - timedelta(days=DIAS_A_GUARDAR)).isoformat()
historial["actualizado"] = hoy.isoformat()
historial.setdefault("juegos", {})

for nombre, url in WEBS.items():
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "replace")
        datos = extraer(nombre, html)
    except Exception as e:
        print(nombre, "ERROR", e)
        continue

    if "error" in datos or not datos.get("numeros"):
        print(nombre, "sin datos:", datos.get("error"))
        continue

    entrada = {
        "iso": datos["iso"],
        "fecha": datos["fecha"],
        "numeros": datos["numeros"],
        "extras": datos["extras"],
        "joker": datos["joker"],
    }
    clave = entrada["iso"] or entrada["fecha"]

    lista = historial["juegos"].setdefault(nombre, [])
    # Quitar el mismo sorteo si ya estaba, y los demasiado antiguos
    lista[:] = [
        e for e in lista
        if (e.get("iso") or e.get("fecha")) != clave
        and not (e.get("iso") and e["iso"] < limite)
    ]
    lista.append(entrada)
    lista.sort(key=lambda e: e.get("iso") or "", reverse=True)
    print(nombre, "OK", entrada["fecha"], "-", len(lista), "sorteos guardados")

with open(RUTA, "w", encoding="utf-8") as f:
    json.dump(historial, f, ensure_ascii=False, indent=2)

print("Guardado", RUTA)
