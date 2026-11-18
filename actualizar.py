import json
import os
import re
import urllib.request
from datetime import date

WEBS = {
    "primitiva": "https://www.combinacionganadora.com/primitiva/",
    "bonoloto": "https://www.combinacionganadora.com/bonoloto/",
    "euromillones": "https://www.combinacionganadora.com/euromillones/",
}

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


def limpiar(fragmento):
    texto = re.sub(r"<[^>]+>", " ", fragmento)
    return re.sub(r"\s+", " ", texto).strip()


def extraer(nombre, html):
    html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)

    # Primero busca la lista de numeros de ese juego; si no, la primera lista "numbers"
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

    # Fecha: la ultima que aparece en el texto justo antes de los numeros
    antes = limpiar(html[max(0, m.start() - 3000): m.start()])
    # La fecha del sorteo mostrado aparece con dia de la semana: "Lunes, 16 noviembre 2026"
    con_dia = FECHA_DIA.findall(antes)
    if con_dia:
        fecha = con_dia[-1]
    else:
        fechas = FECHA.findall(antes)
        fecha = fechas[-1] if fechas else None

    # Texto que sigue a los numeros (para Joker, complementario, etc.)
    despues = limpiar(html[m.end(): m.end() + 600])
    joker = re.search(r"Joker\s*(\d{7})", despues)

    return {
        "fecha": fecha,
        "numeros": numeros,
        "extras": extras,
        "joker": joker.group(1) if joker else None,
    }


os.makedirs("data", exist_ok=True)
salida = {"actualizado": date.today().isoformat(), "juegos": {}}

for nombre, url in WEBS.items():
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "replace")
        datos = extraer(nombre, html)
        datos["fuente"] = url
        salida["juegos"][nombre] = datos
        print(nombre, datos)
    except Exception as e:
        print(nombre, "ERROR", e)
        salida["juegos"][nombre] = {"error": str(e)}

with open("data/resultados.json", "w", encoding="utf-8") as f:
    json.dump(salida, f, ensure_ascii=False, indent=2)

print("Guardado data/resultados.json")
