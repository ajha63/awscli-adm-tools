"""
IAM — Listar roles con su fecha de creación y última actividad.

Uso:
    uv run python -m aws_adm_script.iam.list_roles
    uv run python -m aws_adm_script.iam.list_roles --prefix MyApp
"""

import argparse
import logging
import sys
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from aws_adm_script.utils.session import get_session, verify_identity

logger = logging.getLogger(__name__)


def list_roles(
    session: boto3.Session,
    path_prefix: str = "/",
) -> list[dict[str, Any]]:
    """
    Lista roles IAM filtrados opcionalmente por path prefix.

    Args:
        session:     Sesión boto3 activa.
        path_prefix: Prefijo del path IAM (ej. "/", "/aws-reserved/").

    Returns:
        Lista de dicts con RoleName, RoleId, Path, CreateDate.
    """
    iam = session.client("iam")
    paginator = iam.get_paginator("list_roles")
    roles: list[dict[str, Any]] = []

    for page in paginator.paginate(PathPrefix=path_prefix):
        for role in page["Roles"]:
            roles.append(
                {
                    "RoleName": role["RoleName"],
                    "RoleId": role["RoleId"],
                    "Path": role["Path"],
                    "CreateDate": role["CreateDate"].strftime("%Y-%m-%d"),
                }
            )

    return roles


def _print_table(roles: list[dict[str, Any]]) -> None:
    if not roles:
        print("No se encontraron roles.")
        return

    col_widths = {"RoleName": 40, "RoleId": 22, "Path": 30, "CreateDate": 12}
    header = "  ".join(k.ljust(v) for k, v in col_widths.items())
    sep = "  ".join("-" * v for v in col_widths.values())
    print(header)
    print(sep)
    for role in roles:
        row = "  ".join(str(role[k]).ljust(v) for k, v in col_widths.items())
        print(row)

    print(f"\nTotal: {len(roles)} rol(es)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lista roles IAM")
    parser.add_argument("--profile", default=None, help="Perfil AWS CLI")
    parser.add_argument("--region", default="us-east-1", help="Región AWS")
    parser.add_argument(
        "--prefix", default="/", help="Path prefix IAM (ej. /aws-reserved/)"
    )
    args = parser.parse_args()

    session = get_session(profile=args.profile, region=args.region)

    try:
        verify_identity(session, expected_account_id=None)
    except (BotoCoreError, ClientError) as exc:
        logger.error("Error de autenticación: %s", exc)
        sys.exit(1)

    try:
        roles = list_roles(session, path_prefix=args.prefix)
    except (BotoCoreError, ClientError) as exc:
        logger.error("Error al listar roles: %s", exc)
        sys.exit(1)

    _print_table(roles)


if __name__ == "__main__":
    main()
