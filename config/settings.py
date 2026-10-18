"""
Configuración central del proyecto.

Carga variables desde .env (si existe) y expone
constantes tipadas para el resto de los scripts.
"""

import logging
import os

from dotenv import load_dotenv

# Carga .env desde la raíz del proyecto (no sobreescribe variables ya definidas)
load_dotenv(override=False)

# ── AWS ───────────────────────────────────────────────────────────────────────
AWS_PROFILE: str = os.environ.get("AWS_PROFILE", "alhernan")
AWS_DEFAULT_REGION: str = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
EXPECTED_ACCOUNT_ID: str = os.environ.get("EXPECTED_ACCOUNT_ID", "554982632606")

# ── Logging ───────────────────────────────────────────────────────────────────
_LOG_LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}
LOG_LEVEL: int = _LOG_LEVEL_MAP.get(
    os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO
)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
