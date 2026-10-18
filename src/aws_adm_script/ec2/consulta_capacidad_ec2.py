"""
EC2 — Consulta de capacidad e información de tipos de instancia por región.

Uso:
    uv run python -m aws_adm_script.ec2.consulta_capacidad_ec2 --region us-east-1 --tipoEC2 m5
    uv run python -m aws_adm_script.ec2.consulta_capacidad_ec2 --tipoEC2 t3.medium --formato yaml
    uv run python -m aws_adm_script.ec2.consulta_capacidad_ec2 --tipoEC2 m5.large --verificar-capacidad

Parámetros:
    --region              Región AWS (por defecto: us-east-1).
    --tipoEC2             Familia (ej: m5) o tipo exacto (ej: m5.large). Requerido.
    --formato             Formato de salida: json (por defecto) o yaml.
    --verificar-capacidad Realiza un dry-run de create_capacity_reservation por zona
                          para verificar capacidad real sin crear recursos.
    --profile             Perfil AWS CLI (IAM Identity Center / SSO).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

import boto3
import yaml
from botocore.exceptions import BotoCoreError, ClientError

from aws_adm_script.utils.session import get_session, verify_identity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers de consulta
# ---------------------------------------------------------------------------


def _expandir_familia(ec2_client: Any, tipo_o_familia: str) -> list[str]:
    """
    Dado un tipo exacto (ej: 'm5.large') o una familia (ej: 'm5'),
    devuelve la lista de tipos de instancia que coinciden.

    Si el valor contiene '.' se asume tipo exacto y se retorna tal cual.
    Si no, se usa el wildcard '<familia>.*' para obtener todos los tipos
    de la familia via describe_instance_types con filtro de nombre.
    """
    if "." in tipo_o_familia:
        return [tipo_o_familia]

    # Es una familia: usar wildcard
    paginator = ec2_client.get_paginator("describe_instance_types")
    tipos: list[str] = []
    for page in paginator.paginate(
        Filters=[{"Name": "instance-type", "Values": [f"{tipo_o_familia}.*"]}]
    ):
        for item in page["InstanceTypes"]:
            tipos.append(item["InstanceType"])

    return sorted(tipos)


def _obtener_especificaciones(
    ec2_client: Any,
    tipos: list[str],
) -> dict[str, dict[str, Any]]:
    """
    Consulta describe_instance_types para los tipos indicados.
    Retorna un dict {InstanceType -> specs_dict}.
    """
    specs: dict[str, dict[str, Any]] = {}

    # La API acepta hasta 100 tipos por llamada
    for i in range(0, len(tipos), 100):
        chunk = tipos[i : i + 100]
        response = ec2_client.describe_instance_types(InstanceTypes=chunk)
        for item in response.get("InstanceTypes", []):
            itype = item["InstanceType"]
            specs[itype] = {
                "vCPUs": item.get("VCpuInfo", {}).get("DefaultVCpus"),
                "MemoriaMiB": item.get("MemoryInfo", {}).get("SizeInMiB"),
                "Arquitecturas": item.get("ProcessorInfo", {}).get("SupportedArchitectures", []),
                "RedGbps": item.get("NetworkInfo", {}).get("NetworkPerformance"),
                "Almacenamiento": item.get("InstanceStorageInfo", {}).get("TotalSizeInGB"),
            }

    return specs


def _obtener_zonas(
    ec2_client: Any,
    tipos: list[str],
) -> dict[str, list[str]]:
    """
    Consulta describe_instance_type_offerings para obtener las zonas de
    disponibilidad donde cada tipo de instancia está disponible.
    Retorna {InstanceType -> [zona1, zona2, ...]}.
    """
    paginator = ec2_client.get_paginator("describe_instance_type_offerings")
    zonas: dict[str, list[str]] = {}

    for page in paginator.paginate(
        LocationType="availability-zone",
        Filters=[{"Name": "instance-type", "Values": tipos}],
    ):
        for offering in page["InstanceTypeOfferings"]:
            itype = offering["InstanceType"]
            zona = offering["Location"]
            zonas.setdefault(itype, []).append(zona)

    return {k: sorted(v) for k, v in zonas.items()}


def _verificar_capacidad_por_zona(
    ec2_client: Any,
    tipo: str,
    zonas: list[str],
) -> dict[str, str]:
    """
    Para cada zona, intenta un dry-run de create_capacity_reservation con
    InstanceCount=1. Esto NO crea ningún recurso; solo verifica si AWS
    puede satisfacer la solicitud en esa zona.

    Retorna {zona -> "disponible" | "sin_capacidad" | "error: <msg>"}.
    """
    resultado: dict[str, str] = {}

    for zona in zonas:
        try:
            ec2_client.create_capacity_reservation(
                InstanceType=tipo,
                InstancePlatform="Linux/UNIX",
                AvailabilityZone=zona,
                InstanceCount=1,
                Tenancy="default",
                EndDateType="unlimited",
                DryRun=True,
            )
            # Si no lanza excepción (improbable con DryRun=True), marcar disponible
            resultado[zona] = "disponible"
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code == "DryRunOperation":
                # DryRunOperation significa que el request hubiera sido exitoso
                resultado[zona] = "disponible"
            elif code == "InsufficientCapacityError":
                resultado[zona] = "sin_capacidad"
            else:
                resultado[zona] = f"error: {code}"

    return resultado


# ---------------------------------------------------------------------------
# Función principal de negocio
# ---------------------------------------------------------------------------


def consultar_capacidad(
    session: boto3.Session,
    tipo_ec2: str,
    verificar_capacidad: bool = False,
) -> dict[str, Any]:
    """
    Consulta especificaciones y disponibilidad de una familia o tipo de instancia EC2.

    Args:
        session:             Sesión boto3 activa.
        tipo_ec2:            Familia (m5) o tipo exacto (m5.large).
        verificar_capacidad: Si True, realiza dry-run por zona para verificar
                             capacidad real.

    Returns:
        Dict serializable con región, tipos consultados y sus detalles.
    """
    ec2 = session.client("ec2")
    region = session.region_name or "desconocida"

    logger.info("Expandiendo '%s' en la región '%s'…", tipo_ec2, region)
    tipos = _expandir_familia(ec2, tipo_ec2)

    if not tipos:
        return {
            "region": region,
            "tipoEC2_consultado": tipo_ec2,
            "total_tipos": 0,
            "tipos": [],
        }

    logger.info("Tipos encontrados: %s", tipos)
    specs = _obtener_especificaciones(ec2, tipos)
    zonas_por_tipo = _obtener_zonas(ec2, tipos)

    tipos_resultado: list[dict[str, Any]] = []

    for tipo in sorted(tipos):
        zonas = zonas_por_tipo.get(tipo, [])
        entrada: dict[str, Any] = {
            "tipo": tipo,
            "especificaciones": specs.get(tipo, {}),
            "zonas_disponibles": zonas,
            "total_zonas": len(zonas),
        }

        if verificar_capacidad:
            if zonas:
                entrada["capacidad_por_zona"] = _verificar_capacidad_por_zona(ec2, tipo, zonas)
            else:
                entrada["capacidad_por_zona"] = {}

        tipos_resultado.append(entrada)

    return {
        "region": region,
        "tipoEC2_consultado": tipo_ec2,
        "total_tipos": len(tipos_resultado),
        "tipos": tipos_resultado,
    }


# ---------------------------------------------------------------------------
# Serialización y salida
# ---------------------------------------------------------------------------


def serializar(datos: dict[str, Any], formato: str) -> str:
    """Serializa el resultado a JSON o YAML."""
    if formato == "yaml":
        result: str = yaml.safe_dump(datos, allow_unicode=True, sort_keys=False)
        return result
    return json.dumps(datos, indent=2, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Punto de entrada CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta capacidad e información de tipos de instancia EC2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--profile", default=None, help="Perfil AWS CLI (IAM Identity Center)")
    parser.add_argument("--region", default="us-east-1", help="Región AWS (default: us-east-1)")
    parser.add_argument(
        "--tipoEC2",
        required=True,
        metavar="TIPO_O_FAMILIA",
        help="Familia (ej: m5) o tipo exacto (ej: m5.large)",
    )
    parser.add_argument(
        "--formato",
        choices=["json", "yaml"],
        default="json",
        help="Formato de salida: json (default) o yaml",
    )
    parser.add_argument(
        "--verificar-capacidad",
        action="store_true",
        default=False,
        help="Realiza dry-run de create_capacity_reservation por zona para "
        "verificar capacidad real (no crea recursos)",
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
        resultado = consultar_capacidad(
            session,
            tipo_ec2=args.tipoEC2,
            verificar_capacidad=args.verificar_capacidad,
        )
    except (BotoCoreError, ClientError) as exc:
        logger.error("Error al consultar capacidad EC2: %s", exc)
        sys.exit(1)

    print(serializar(resultado, args.formato))


if __name__ == "__main__":
    main()
