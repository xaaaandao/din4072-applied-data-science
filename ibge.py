import requests


def get_data_ibge():
    try:
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
        return requests.get(url)
    except Exception:
        raise requests.exceptions.RequestException("error in request")

def get_sigla(response):
    return response["microrregiao"]["mesorregiao"]["UF"]["sigla"] if "microrregiao" in response and response["microrregiao"] else None

def get_nome_uf(response):
    return response["microrregiao"]["mesorregiao"]["UF"]["nome"] if "microrregiao" in response and response["microrregiao"] else None