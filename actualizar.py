import re
import urllib.error
import urllib.request

WEBS = [
    "https://www.combinacionganadora.com/",
    "https://www.combinacionganadora.com/primitiva/",
    "https://www.combinacionganadora.com/bonoloto/",
    "https://www.combinacionganadora.com/euromillones/",
    "https://loteriabonoloto.info/",
    "https://laprimitiva.info/",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "es-ES,es;q=0.9",
}

for url in WEBS:
    print("---", url)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "replace")
        texto = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
        texto = re.sub(r"<[^>]+>", " ", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        print("OK", r.status, len(html), "caracteres")
        print(texto[:250])
    except urllib.error.HTTPError as e:
        print("ERROR HTTP", e.code)
    except Exception as e:
        print("ERROR", e)
