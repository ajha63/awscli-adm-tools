"""
EC2 — Listar instancias por región con filtros opcionales.

Uso:
    uv run python -m aws_adm_script.ec2.list_instances
    uv run python -m aws_adm_script.ec2.list_instances --state running --region us-east-1
"""

import argparse
import logging
import sys
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from mypy_boto3_ec2.type_defs import FilterTypeDef

from aws_adm_script.utils.session import get_session, verify_identity

logger = logging.getLogger(__name__)


def list_instances(
    session: boto3.Session,
    state_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Retorna instancias EC2 en la región de la sesión.

    Args:
        session:      Sesión boto3 activa.
        state_filter: Estado a filtrar (running, stopped, terminated, ...).
                      None = todas las instancias.

    Returns:
        Lista de dicts con Id, Name, State, Type, LaunchTime.
    """
    ec2 = session.client("ec2")
    filters: list[FilterTypeDef] = []

    if state_filter:
        filters.append({"Name": "instance-state-name", "Values": [state_filter]})

    paginator = ec2.get_paginator("describe_instances")
    instances: list[dict[str, Any]] = []

    for page in paginator.paginate(Filters=filters):
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                name = next(
                    (tag["Value"] for tag in inst.get("Tags", []) if tag["Key"] == "Name"),
                    "—",
                )
                instances.append(
                    {
                        "Id": inst["InstanceId"],
                        "Name": name,
                        "State": inst["State"]["Name"],
                        "Type": inst["InstanceType"],
                        "LaunchTime": inst["LaunchTime"].isoformat(),
                    }
                )

    return instances


def _print_table(instances: list[dict[str, Any]]) -> None:
    if not instances:
        print("No se encontraron instancias.")
        return

    col_widths = {"Id": 21, "Name": 30, "State": 12, "Type": 14, "LaunchTime": 26}
    header = "  ".join(k.ljust(v) for k, v in col_widths.items())
    sep = "  ".join("-" * v for v in col_widths.values())
    print(header)
    print(sep)
    for inst in instances:
        row = "  ".join(str(inst[k]).ljust(v) for k, v in col_widths.items())
        print(row)

    print(f"\nTotal: {len(instances)} instancia(s)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lista instancias EC2")
    parser.add_argument("--profile", default=None, help="Perfil AWS CLI")
    parser.add_argument("--region", default="us-east-1", help="Región AWS")
    parser.add_argument(
        "--state",
        default=None,
        choices=["running", "stopped", "terminated", "pending", "shutting-down"],
        help="Filtrar por estado",
    )
    args = parser.parse_args()

    session = get_session(profile=args.profile, region=args.region)

    try:
        verify_identity(session, expected_account_id=None)
    except (BotoCoreError, ClientError) as exc:
        logger.error("Error de autenticación: %s", exc)
        sys.exit(1)

    try:
        instances = list_instances(session, state_filter=args.state)
    except (BotoCoreError, ClientError) as exc:
        logger.error("Error al listar instancias: %s", exc)
        sys.exit(1)

    _print_table(instances)


if __name__ == "__main__":
    main()
