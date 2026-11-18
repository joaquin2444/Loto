import re
import urllib.request

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

# Busca 5 o 6 números seguidos (una combinación ganadora)
PATRON = re.compile(r"(?:\b\d{1,2}\b\W{1,6}){5,6}\b\d{1,2}\b")

for nombre, url in WEBS.items():
    print("=====", nombre)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "replace")

        # Quitar scripts y estilos
        limpio = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)

        # Texto plano
        texto = re.sub(r"<[^>]+>", " ", limpio)
        texto = re.sub(r"\s+", " ", texto)
        m = PATRON.search(texto)
        if m:
            print("TEXTO:", texto[max(0, m.start() - 150): m.end() + 250])
        else:
            print("TEXTO: no encontrado")

        # HTML crudo alrededor de los números (para ver las etiquetas)
        h = re.sub(r"\s+", " ", limpio)
        m2 = re.search(r"(?:<li[^>]*>\s*\d{1,2}\s*</li>\s*){5}", h)
        if m2:
            print("HTML:", h[max(0, m2.start() - 200): m2.end() + 300])
        else:
            print("HTML: no encontrado el patron de <li>")
    except Exception as e:
        print("ERROR", e)
