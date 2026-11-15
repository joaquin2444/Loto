import urllib.request

PRUEBAS = [
    ("primitiva", "LAPR", "20261114"),
    ("bonoloto", "BONO", "20261114"),
    ("euromillones", "EMIL", "20261113"),
]
BASE = "https://www.loteriasyapuestas.es/f/loterias/resultados/"

for nombre, codigo, fecha in PRUEBAS:
    url = BASE + nombre + ".html?game_id=" + codigo + "&fecha_sorteo=" + fecha
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            texto = r.read().decode("utf-8", "replace")
            print(nombre, "OK", r.status, len(texto), "caracteres")
            print(texto[:300].replace("\n", " "))
    except Exception as e:
        print(nombre, "ERROR", e)
