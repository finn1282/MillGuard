"""Download MetroPT-3 (UCI id 791, CC BY 4.0) into backend/data/metropt/ (gitignored).
ucimlrepo reports this dataset as not importable, so we use the UCI static zip."""
import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data" / "metropt"
URL = "https://archive.ics.uci.edu/static/public/791/metropt+3+dataset.zip"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    local = OUT / "metropt3.zip"   # `make fetch-metropt` resumes this with curl; the UCI server can be slow
    raw = local.read_bytes() if local.exists() else urllib.request.urlopen(URL, timeout=600).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        df = pd.read_csv(z.open(name))
    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")])
    df.to_parquet(OUT / "metropt3.parquet")
    print(df.shape, list(df.columns))


if __name__ == "__main__":
    main()
