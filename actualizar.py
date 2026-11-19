import re
import urllib.error
import urllib.request

BASE = "https://www.combinacionganadora.com/"
PAGINAS = ["", "bote/", "botes/", "primitiva/"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "es-ES,es;q=0.9",
}


def limpiar(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", h)


for ruta in PAGINAS:
    url = BASE + ruta
    print("=====", url)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "replace")
        print("OK", r.status, len(html), "caracteres")

        enlaces = sorted(set(re.findall(r'href="([^"]*bote[^"]*)"', html, flags=re.I)))
        print("ENLACES con 'bote':", enlaces[:8])

        texto = limpiar(html)
        n = 0
        for m in re.finditer(r"bote", texto, flags=re.I):
            fragmento = texto[max(0, m.start() - 80): m.end() + 140]
            if re.search(r"\d", fragmento):
                print("BOTE:", fragmento)
                n += 1
            if n >= 5:
                break
        if n == 0:
            print("No hay fragmentos con 'bote' y cifras")

        if ruta == "primitiva/":
            i = texto.find("Siguiente sorteo")
            print("SIGUIENTE:", texto[max(0, i - 100): i + 300] if i >= 0 else "no aparece")
    except urllib.error.HTTPError as e:
        print("ERROR HTTP", e.code)
    except Exception as e:
        print("ERROR", e)
