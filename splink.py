import os

import pandas as pd

from utils import make_request


def download_specieslink():
    start = 0
    increment = 100
    limits = increment - 1

    os.makedirs("parquet", exist_ok=True)

    i = 0
    while True:
        print("start: %d limits: %d " % (start, limits))

        url = "https://specieslink.net/ws/1.0/search?apikey=%s&offset=%d&limits=%d&kingdom=Plantae" % (os.environ["SPLINK"], start, limits)
        response = make_request(url)

        if len(response["features"]) == 0:
            break

        props = [r["properties"] for r in response["features"]]
        df = pd.DataFrame(props)
        os.makedirs("./parquet", exist_ok=True)
        filename = os.path.join("./parquet", "%d.parquet" % i)
        if not os.path.exists(filename):
            df.to_parquet(filename, index=False)
            print(filename)

        i = i + 1
        start = limits + 1
        limits = (start + increment) - 1


def load_parquet(conn, local_file):
    pass