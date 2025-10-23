import requests

def make_request(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            json = response.json()
            if len(json) > 0:
                return json
    except requests.exceptions:
        raise ValueError


