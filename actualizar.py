import re
import urllib.error
import urllib.request

BASE = "https://www.combinacionganadora.com/"
CANDIDATAS = [
    "gordo-primitiva/",
    "el-gordo-de-la-primitiva/",
    "gordo/",
    "eurodreams/",
    "euro-dreams/",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "es-ES,es;q=0.9",
}

for ruta in CANDIDATAS:
    url = BASE + ruta
    print("=====", url)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "replace")
        print("OK", r.status, len(html), "caracteres")
        html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
        html = re.sub(r"\s+", " ", html)
        print("gametype:", re.findall(r'data-gametype="([^"]+)"', html)[:4])
        m = re.search(r'<ul[^>]*data-gametype="[^"]+"[^>]*>.*?</ul>', html)
        if m:
            print("LISTA:", m.group(0)[:900])
            sig = html[m.end(): m.end() + 300]
            print("DESPUES:", re.sub(r"<[^>]+>", " ", sig)[:150])
        else:
            print("LISTA: no encontrada")
        t = re.sub(r"<[^>]+>", " ", html)
        d = re.findall(
            r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo),? \d{1,2} [a-záéíóúñ]+ \d{4}",
            t, flags=re.I)
        print("FECHAS:", d[:2])
    except urllib.error.HTTPError as e:
        print("ERROR HTTP", e.code)
    except Exception as e:
        print("ERROR", e)
