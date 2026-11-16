import time
import urllib.request

PAGINAS = {
    "https://clar1x.github.io/suscetirmr/": {
        "tem": ["Registros e ausências", "Já existem mapas", "Pfaltzgraff", "Registros históricos de deslizamentos",
                "Escopo.", "Cobertura.", "reservado para a avaliação final", "consulta por clique", "exportar_relevo"],
        "nao": ["s registros históricos se", "Inventário histórico de deslizamentos", "uma única vez",
                "Faltam mapas", "GEGEP", "[Autores]", "conferir", "COLAR AQUI"],
    },
    "https://clar1x.github.io/suscetirmr/mapa/": {
        "tem": ["Cobertura atual", "Como usar", "Relevo sombreado do PE3D", "Documentação completa no <a"],
        "nao": ["documentação no GitHub", "Comparar as duas versões", "tabela-municipios", "GEGEP"],
    },
}


def baixar(url):
    pedido = urllib.request.Request(f"{url}?x={int(time.time())}", headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(pedido, timeout=30).read().decode("utf-8")


for url, regras in PAGINAS.items():
    html = baixar(url)
    print(f"\n{url}")
    for texto in regras["tem"]:
        print(("ok     tem: " if texto in html else "FALTA  tem: ") + texto)
    for texto in regras["nao"]:
        print(("FALHA  não deveria ter: " if texto in html else "ok     não tem: ") + texto)