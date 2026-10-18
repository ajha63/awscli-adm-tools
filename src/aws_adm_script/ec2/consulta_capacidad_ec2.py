"""
EC2 — Consulta de capacidad disponible por tipo de instancia y región.

Uso:
    uv run python -m aws_adm_script.ec2.consulta_capacidad_ec2
    uv run python -m aws_adm_script.ec2.consulta_capacidad_ec2 --instance-type t3.medium --region us-east-1
"""

import argparse
import logging
import sys
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from aws_adm_script.utils.session import get_session, verify_identity

logger = logging.getLogger(__name__)


def consulta_capacidad(
    session: Any,
    instance_types: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Consulta la capacidad disponible de tipos de instancia EC2 en la región de la sesión.

    Usa describe_instance_type_offerings para verificar disponibilidad por zona
    y describe_instance_types para obtener detalles de vCPU y memoria.

    Args:
        session:        Sesión boto3 activa.
        instance_types: Lista de tipos a consultar (ej. ["t3.medium", "m5.large"]).
                        None = todos los tipos disponibles.

    Returns:
        Lista de dicts con InstanceType, vCPUs, MemoryMiB y zonas disponibles.
    """
    ec2 = session.client("ec2")

    # --- Obtener zonas de disponibilidad por tipo ---
    offerings_kwargs: dict[str, Any] = {"LocationType": "availability-zone"}
    if instance_types:
        offerings_kwargs["Filters"] = [{"Name": "instance-type", "Values": instance_types}]

    paginator = ec2.get_paginator("describe_instance_type_offerings")
    zones_by_type: dict[str, list[str]] = {}

    for page in paginator.paginate(**offerings_kwargs):
        for offering in page["InstanceTypeOfferings"]:
            itype = offering["InstanceType"]
            zone = offering["Location"]
            zones_by_type.setdefault(itype, []).append(zone)

    if not zones_by_type:
        return []

    # --- Obtener detalles de vCPU y memoria ---
    types_to_describe = list(zones_by_type.keys())
    details_kwargs: dict[str, Any] = {"InstanceTypes": types_to_describe}

    response = ec2.describe_instance_types(**details_kwargs)
    results: list[dict[str, Any]] = []

    for item in response.get("InstanceTypes", []):
        itype = item["InstanceType"]
        vcpus = item.get("VCpuInfo", {}).get("DefaultVCpus", "—")
        memory_mib = item.get("MemoryInfo", {}).get("SizeInMiB", "—")
        zones = sorted(zones_by_type.get(itype, []))

        results.append(
            {
                "InstanceType": itype,
                "vCPUs": vcpus,
                "MemoryMiB": memory_mib,
                "ZonasDisponibles": ", ".join(zones),
                "TotalZonas": len(zones),
            }
        )

    # Ordenar por tipo de instancia
    results.sort(key=lambda x: x["InstanceType"])
    return results


def _print_table(results: list[dict[str, Any]]) -> None:
    if not results:
        print("No se encontraron tipos de instancia disponibles.")
        return

    col_widths = {
        "InstanceType": 20,
        "vCPUs": 7,
        "MemoryMiB": 11,
        "TotalZonas": 11,
        "ZonasDisponibles": 50,
    }
    header = "  ".join(k.ljust(v) for k, v in col_widths.items())
    sep = "  ".join("-" * v for v in col_widths.values())
    print(header)
    print(sep)
    for row in results:
        line = "  ".join(str(row[k]).ljust(v) for k, v in col_widths.items())
        print(line)

    print(f"\nTotal: {len(results)} tipo(s) de instancia")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta capacidad disponible de tipos de instancia EC2"
    )
    parser.add_argument("--profile", default=None, help="Perfil AWS CLI")
    parser.add_argument("--region", default="us-east-1", help="Región AWS")
    parser.add_argument(
        "--instance-type",
        dest="instance_types",
        nargs="+",
        metavar="TYPE",
        default=None,
        help="Uno o más tipos de instancia (ej: t3.medium m5.large). Omitir para consultar todos.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s — %(message)s")

    session = get_session(profile=args.profile, region=args.region)

    try:
        verify_identity(session, expected_account_id=None)
    except (BotoCoreError, ClientError) as exc:
        logger.error("Error de autenticación: %s", exc)
        sys.exit(1)

    try:
        results = consulta_capacidad(session, instance_types=args.instance_types)
    except (BotoCoreError, ClientError) as exc:
        logger.error("Error al consultar capacidad EC2: %s", exc)
        sys.exit(1)

    _print_table(results)


if __name__ == "__main__":
    main()
