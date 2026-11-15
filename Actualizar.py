import json, re, os, sys, urllib.request
from datetime import date, timedelta

JUEGOS = {"primitiva": "LAPR", "bonoloto": "BONO",
          "euromillones": "EMIL", "gordo": "ELGR"}
URL = ("https://www.loteriasyapuestas.es/servicios/buscadorSorteos"
       "?game_id={}&fechaInicioInclusiva={}&fechaFinInclusiva={}&celebrados=true")
ARCHIVO = "data/resultados.json"


def partir(juego, n):
    if juego in ("primitiva", "bonoloto") and len(n) >= 8:
        return {"n": n[:6], "c": n[6:7], "r": n[7:8]}
    if juego == "euromillones" and len(n) >= 7:
        return {"n": n[:5], "e": n[5:7]}
    if juego == "gordo" and len(n) >= 6:
        return {"n": n[:5], "k": n[5:6]}
    return None


def main():
    dias = int(os.environ.get("DIAS", "45"))
    fin = date.today()
    ini = fin - timedelta(days=dias)
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            datos = json.load(f)
    except Exception:
        datos = []
    por_clave = {(x["g"], x["d"]): x for x in datos}
    errores = 0
    for juego, codigo in JUEGOS.items():
        url = URL.format(codigo, ini.strftime("%Y%m%d"), fin.strftime("%Y%m%d"))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                lista = json.loads(r.read().decode("utf-8"))
            if not isinstance(lista, list):
                raise ValueError("respuesta inesperada")
        except Exception as e:
            print("Error en", juego, e)
            errores += 1
            continue
        nuevos = 0
        for s in lista:
            nums = [int(x) for x in re.findall(r"\d+", s.get("combinacion", ""))]
            v = partir(juego, nums)
            fecha = str(s.get("fecha_sorteo", ""))[:10]
            if v and fecha:
                if (juego, fecha) not in por_clave:
                    nuevos += 1
                por_clave[(juego, fecha)] = {"id": juego + fecha, "g": juego, "d": fecha, "v": v}
        print(juego, len(lista), "sorteos leidos,", nuevos, "nuevos")
    os.makedirs("data", exist_ok=True)
    salida = sorted(por_clave.values(), key=lambda x: x["d"], reverse=True)
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False)
    if errores == len(JUEGOS):
        sys.exit(1)


main()
