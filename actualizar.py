import json
import os
import re
import time
import urllib.request
from datetime import date, timedelta

WEBS = {
    "primitiva": "https://www.combinacionganadora.com/primitiva/",
    "elgordo": "https://www.combinacionganadora.com/elgordo/",
    "bonoloto": "https://www.combinacionganadora.com/bonoloto/",
    "euromillones": "https://www.combinacionganadora.com/euromillones/",
    "eurodreams": "https://www.combinacionganadora.com/eurodreams/",
    "loterianacional": [
        "https://www.combinacionganadora.com/loterianacional/",
        "https://www.combinacionganadora.com/loteria-nacional/",
    ],
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
    "Referer": "https://www.google.com/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
}

BLOQUEADO = False


def descargar(url, intentos=3):
    """Descarga una pagina con reintentos. Si ya se detecto un bloqueo (403), no insiste."""
    global BLOQUEADO
    if BLOQUEADO:
        intentos = 1
    ultimo = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            ultimo = e
            if i < intentos - 1:
                time.sleep(10 * (i + 1))
    if "403" in str(ultimo):
        BLOQUEADO = True
    raise ultimo


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


def valido(e):
    """Un sorteo es valido si todos sus numeros son cifras (no '?' de un sorteo pendiente)."""
    if "primero" in e:
        premio = r"\d{2}\.\d{3}|\d{5}"
        return (
            re.fullmatch(premio, str(e.get("primero")))
            and re.fullmatch(premio, str(e.get("segundo")))
            and len(e.get("cifras4") or []) > 0
            and len(e.get("cifras3") or []) > 0
            and len(e.get("cifras2") or []) > 0
        ) is not None
    numeros = e.get("numeros") or []
    extras = e.get("extras") or []
    return (
        len(numeros) > 0
        and all(re.fullmatch(r"\d+", str(n)) for n in numeros)
        and all(re.fullmatch(r"[A-Z]\s*\d+", str(x)) for x in extras)
    )


def buscar_joker(texto):
    """Busca el Joker (7 cifras) en un texto limpio, aunque venga con separadores."""
    for m in re.finditer(r"Joker\W{0,6}((?:\d\W{0,2}){7})", texto):
        cifras = re.sub(r"\D", "", m.group(1))
        if len(cifras) == 7:
            return cifras
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
    etiquetas = {}
    for attrs, contenido in re.findall(r"<li([^>]*)>(.*?)</li>", m.group(1), flags=re.S):
        valor = limpiar(contenido)
        if not valor:
            continue
        if "data-extra" in attrs:
            extras.append(valor)
            titulo = re.search(r'title="([^"]+)"', contenido)
            letra = re.match(r"([A-Z])", valor)
            if titulo and letra:
                etiquetas[letra.group(1)] = titulo.group(1)
        else:
            numeros.append(valor)

    antes = limpiar(html[max(0, m.start() - 3000): m.start()])
    con_dia = FECHA_DIA.findall(antes)
    if con_dia:
        fecha = con_dia[-1]
    else:
        fechas = FECHA.findall(antes)
        fecha = fechas[-1] if fechas else None

    # Texto que sigue a la lista de numeros (ventana amplia, ya sin etiquetas HTML)
    despues = limpiar(html[m.end(): m.end() + 8000])[:3000]
    joker = buscar_joker(despues) if nombre == "primitiva" else None
    if nombre == "primitiva" and not joker:
        print("Joker no encontrado. Texto tras los numeros:", despues[:300])

    return {
        "fecha": fecha,
        "iso": a_iso(fecha),
        "numeros": numeros,
        "extras": extras,
        "etiquetas": etiquetas,
        "joker": joker,
    }


def extraer_nacional(html):
    html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    texto = limpiar(html)

    # Primer y segundo premio (en cualquiera de los dos ordenes posibles)
    m = re.search(
        r"primer premio\W+(?:segundo premio\W+)?(\d{2}\.\d{3})\W+(?:segundo premio\W+)?(\d{2}\.\d{3})",
        texto, flags=re.I)
    if not m:
        return {"error": "no se encontraron el primer y segundo premio"}

    antes = texto[max(0, m.start() - 400): m.start()]
    con_dia = FECHA_DIA.findall(antes)
    fecha = con_dia[-1] if con_dia else None

    resto = texto[m.end():]

    def pos(patron, desde=0):
        mm = re.search(patron, resto[desde:], flags=re.I)
        return (desde + mm.start(), desde + mm.end()) if mm else None

    p4 = pos(r"[úu]ltimas\s*4\s*cifras")
    if not p4:
        return {"error": "no aparece 'Ultimas 4 cifras'"}
    p3 = pos(r"[úu]ltimas\s*3\s*cifras", p4[1])
    p2 = pos(r"[úu]ltimas\s*2\s*cifras", p3[1]) if p3 else None
    pr = pos(r"reintegros?", p2[1]) if p2 else None
    if not (p3 and p2):
        return {"error": "faltan las secciones de 3 o 2 cifras"}

    cifras4 = re.findall(r"\b\d{4}\b", resto[p4[1]: p3[0]])
    cifras3 = re.findall(r"\b\d{3}\b", resto[p3[1]: p2[0]])
    fin2 = pr[0] if pr else p2[1] + 200
    cifras2 = re.findall(r"\b\d{2}\b", resto[p2[1]: fin2])
    reintegros = []
    if pr:
        reintegros = re.findall(r"\b\d\b", resto[pr[1]: pr[1] + 30])[:3]

    return {
        "fecha": fecha,
        "iso": a_iso(fecha),
        "primero": m.group(1),
        "segundo": m.group(2),
        "cifras4": cifras4,
        "cifras3": cifras3,
        "cifras2": cifras2,
        "reintegros": reintegros,
    }


URL_BOTES = "https://www.combinacionganadora.com/botes/"
RUTA_BOTES = "data/botes.json"
DIA_BOTE = r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo),? \d{1,2} [a-záéíóúñ]+ \d{4}"
NOMBRES_BOTE = {
    "primitiva": r"(?<!Gordo de )(?<!Gordo de la )(?:La )?Primitiva",
    "elgordo": r"El Gordo(?: de la Primitiva)?",
    "bonoloto": r"Bonoloto",
    "euromillones": r"Euromillones",
    "eurodreams": r"Euro ?dreams",
}


def extraer_botes(html):
    """Lee la lista 'Botes actualmente en juego': nombre, importe y fecha del proximo sorteo."""
    texto = limpiar(re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S))
    botes = {}
    for clave, nombre in NOMBRES_BOTE.items():
        m = re.search(
            r"(?:" + nombre + r")\s+(\d[\d.,]*\s?M?)\s?€\s+(" + DIA_BOTE + r")",
            texto, flags=re.I)
        if m:
            botes[clave] = {
                "importe": re.sub(r"\s+", "", m.group(1)) + " €",
                "fecha": m.group(2),
                "iso": a_iso(m.group(2)),
            }
    return botes


# Cargar el historial que ya existe
os.makedirs("data", exist_ok=True)
historial = {"actualizado": "", "juegos": {}}
if os.path.exists(RUTA):
    try:
        with open(RUTA, encoding="utf-8") as f:
            historial = json.load(f)
    except Exception as e:
        print("No se pudo leer el historial, se empieza de nuevo:", e)

for _nombre in list(historial.get("juegos", {})):
    historial["juegos"][_nombre] = [e for e in historial["juegos"][_nombre] if valido(e)]

hoy = date.today()
limite = (hoy - timedelta(days=DIAS_A_GUARDAR)).isoformat()
historial["actualizado"] = hoy.isoformat()
historial.setdefault("juegos", {})

for nombre, url in WEBS.items():
    urls = url if isinstance(url, list) else [url]
    html = None
    for u in urls:
        try:
            html = descargar(u)
            break
        except Exception as e:
            print(nombre, "ERROR", u, e)
    if html is None:
        continue

    es_nacional = nombre == "loterianacional"
    datos = extraer_nacional(html) if es_nacional else extraer(nombre, html)

    if "error" in datos:
        print(nombre, "sin datos:", datos["error"])
        continue

    if not valido(datos):
        print(nombre, "sorteo todavia sin resultados, se omite")
        continue

    if es_nacional:
        entrada = {k: datos[k] for k in (
            "iso", "fecha", "primero", "segundo", "cifras4", "cifras3", "cifras2", "reintegros")}
    else:
        entrada = {
            "iso": datos["iso"],
            "fecha": datos["fecha"],
            "numeros": datos["numeros"],
            "extras": datos["extras"],
            "etiquetas": datos.get("etiquetas", {}),
            "joker": datos["joker"],
        }
    clave = entrada["iso"] or entrada["fecha"]

    lista = historial["juegos"].setdefault(nombre, [])

    # Si ya habia un Joker guardado para este mismo sorteo, no se pierde
    if nombre == "primitiva" and not entrada.get("joker"):
        for e in lista:
            if (e.get("iso") or e.get("fecha")) == clave and e.get("joker"):
                entrada["joker"] = e["joker"]
                break

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

# Botes de los proximos sorteos (si falla, se conserva el archivo anterior)
try:
    html_botes = descargar(URL_BOTES)
    botes_actuales = extraer_botes(html_botes)
    if botes_actuales:
        with open(RUTA_BOTES, "w", encoding="utf-8") as f:
            json.dump({"actualizado": hoy.isoformat(), "botes": botes_actuales},
                      f, ensure_ascii=False, indent=2)
        print("Botes guardados:", {k: v["importe"] for k, v in botes_actuales.items()})
    else:
        print("Botes: no se encontro ninguno en la pagina")
except Exception as e:
    print("Botes ERROR", e)
