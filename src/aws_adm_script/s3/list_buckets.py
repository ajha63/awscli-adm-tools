"""
S3 — Listar buckets y su región, tamaño estimado y estado de versionado.

Uso:
    uv run python -m aws_adm_script.s3.list_buckets
    uv run python -m aws_adm_script.s3.list_buckets --profile alhernan
"""

import argparse
import logging
import sys
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from aws_adm_script.utils.session import get_session, verify_identity

logger = logging.getLogger(__name__)


def list_buckets(session: boto3.Session) -> list[dict[str, Any]]:
    """
    Retorna lista de buckets S3 con región y estado de versionado.

    Args:
        session: Sesión boto3 activa.

    Returns:
        Lista de dicts con Name, Region, Versioning, CreationDate.
    """
    s3 = session.client("s3")
    response = s3.list_buckets()
    buckets: list[dict[str, Any]] = []

    for bucket in response.get("Buckets", []):
        name: str = bucket["Name"]

        # Región
        try:
            loc = s3.get_bucket_location(Bucket=name)
            region: str = loc["LocationConstraint"] or "us-east-1"
        except ClientError:
            region = "acceso-denegado"

        # Versionado
        try:
            ver = s3.get_bucket_versioning(Bucket=name)
            versioning: str = ver.get("Status", "Disabled")
        except ClientError:
            versioning = "acceso-denegado"

        buckets.append(
            {
                "Name": name,
                "Region": region,
                "Versioning": versioning,
                "CreationDate": bucket["CreationDate"].strftime("%Y-%m-%d"),
            }
        )

    return buckets


def _print_table(buckets: list[dict[str, Any]]) -> None:
    if not buckets:
        print("No se encontraron buckets.")
        return

    col_widths = {"Name": 45, "Region": 18, "Versioning": 12, "CreationDate": 12}
    header = "  ".join(k.ljust(v) for k, v in col_widths.items())
    sep = "  ".join("-" * v for v in col_widths.values())
    print(header)
    print(sep)
    for b in buckets:
        row = "  ".join(str(b[k]).ljust(v) for k, v in col_widths.items())
        print(row)

    print(f"\nTotal: {len(buckets)} bucket(s)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lista buckets S3")
    parser.add_argument("--profile", default=None, help="Perfil AWS CLI")
    parser.add_argument("--region", default="us-east-1", help="Región de la sesión")
    args = parser.parse_args()

    session = get_session(profile=args.profile, region=args.region)

    try:
        verify_identity(session, expected_account_id=None)
    except (BotoCoreError, ClientError) as exc:
        logger.error("Error de autenticación: %s", exc)
        sys.exit(1)

    try:
        buckets = list_buckets(session)
    except (BotoCoreError, ClientError) as exc:
        logger.error("Error al listar buckets: %s", exc)
        sys.exit(1)

    _print_table(buckets)


if __name__ == "__main__":
    main()
