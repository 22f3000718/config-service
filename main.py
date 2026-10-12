from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS: lets the grader's web page call your API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- The four layers, weakest to strongest ----
DEFAULTS = {"port": 8000, "workers": 1, "debug": False,
            "log_level": "info", "api_key": "default-secret-000"}

YAML_LAYER = {"port": "8926", "api_key": "key-4uqfer4ucc"}

DOTENV_LAYER = {"APP_PORT": "8052", "NUM_WORKERS": "1", "APP_DEBUG": "false"}

OS_ENV_LAYER = {"APP_LOG_LEVEL": "error", "APP_API_KEY": "key-s8ipky9n4z"}

ALIASES = {"NUM_WORKERS": "workers"}


def clean_keys(layer):
    """Turn APP_PORT -> port, NUM_WORKERS -> workers, etc."""
    out = {}
    for k, v in layer.items():
        if k in ALIASES:
            out[ALIASES[k]] = v
        elif k.startswith("APP_"):
            out[k[4:].lower()] = v
        else:
            out[k.lower()] = v
    return out


def coerce(key, value):
    """Convert text into the right type."""
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return str(value).strip().lower() in ("true", "1", "yes", "on")
    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    merged = dict(DEFAULTS)

    # Later layers overwrite earlier ones
    for layer in (clean_keys(YAML_LAYER),
                  clean_keys(DOTENV_LAYER),
                  clean_keys(OS_ENV_LAYER)):
        merged.update(layer)

    # CLI overrides: "port=9000" -> split on the FIRST "=" only
    for item in set:
        if "=" in item:
            k, v = item.split("=", 1)
            merged[k.strip()] = v

    # Fix types, then hide the secret
    result = {k: coerce(k, v) for k, v in merged.items()}
    result["api_key"] = "****"
    return result