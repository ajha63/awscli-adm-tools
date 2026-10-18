"""
Gestión de sesión boto3 con validación de identidad.

Regla de seguridad: SIEMPRE verificar account ID y rol activo
antes de ejecutar cualquier operación sobre AWS.
"""

import logging
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from mypy_boto3_ec2 import EC2Client  # noqa: F401 — re-exportado para type hints

logger = logging.getLogger(__name__)


def get_session(profile: str | None = None, region: str | None = None) -> boto3.Session:
    """
    Crea una sesión boto3 usando el perfil AWS CLI indicado.

    Args:
        profile: Nombre del perfil AWS CLI (IAM Identity Center / SSO).
                 Si es None usa AWS_PROFILE o el perfil por defecto.
        region:  Región AWS. Si es None usa AWS_DEFAULT_REGION o la del perfil.

    Returns:
        Sesión boto3 configurada.
    """
    session = boto3.Session(profile_name=profile, region_name=region)
    logger.debug("Sesión creada — profile=%s region=%s", profile, region)
    return session


def verify_identity(
    session: boto3.Session,
    expected_account_id: str | None = None,
) -> dict[str, str]:
    """
    Verifica la identidad activa con STS y opcionalmente valida el account ID.

    Args:
        session:             Sesión boto3 activa.
        expected_account_id: Si se proporciona, aborta si el account ID no coincide.

    Returns:
        Dict con UserId, Account y Arn de la identidad activa.

    Raises:
        SystemExit: Si el account ID no coincide con el esperado.
    """
    try:
        sts = session.client("sts")
        identity: dict[str, str] = sts.get_caller_identity()
    except (BotoCoreError, ClientError) as exc:
        logger.error("No se pudo obtener la identidad AWS: %s", exc)
        raise

    account = identity["Account"]
    arn = identity["Arn"]

    logger.info("Identidad activa — Account: %s | ARN: %s", account, arn)

    if expected_account_id and account != expected_account_id:
        logger.error(
            "Account ID inesperado: obtenido=%s esperado=%s — abortando.",
            account,
            expected_account_id,
        )
        sys.exit(1)

    return identity
