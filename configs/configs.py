from os import getcwd
from yaml import safe_load

with open(f"{getcwd()}/configs/cred.yaml", "r") as fs:
    cred=safe_load(fs)
class Config:
    TOKEN = cred['Token']
    DEFAULT_PREFIX = "!"
    # OWNER_IDS = [int(id) for id in os.getenv("OWNER_IDS", "").split(",")]