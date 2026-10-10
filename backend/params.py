from pathlib import Path
import yaml

PATH = Path(__file__).parent / "params.yaml"


def load(path=PATH) -> dict:
    return yaml.safe_load(open(path))


def val(p: dict, section: str, key: str):
    return p[section][key]["value"]
