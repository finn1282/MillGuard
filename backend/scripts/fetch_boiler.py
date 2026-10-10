"""Download the real boiler dataset (Scientific Data 2025, figshare 28822793). Never committed: backend/data/ is gitignored."""
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parents[1] / "data" / "boiler" / "xinan_completed_data.csv"
URL = "https://ndownloader.figshare.com/files/53778512"


def main():
    if DEST.exists():
        return DEST
    DEST.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(URL, DEST)
    return DEST


if __name__ == "__main__":
    print(main())
