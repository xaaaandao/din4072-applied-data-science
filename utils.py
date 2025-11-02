import requests

def make_requests(base_url):
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            j = response.json()
            if len(j) > 0:
                return j
    except:
        raise ValueError
    
def clean_json(obj):
    if isinstance(obj, dict):
        if not obj:
            return None
        return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json(item) for item in obj]
    return obj