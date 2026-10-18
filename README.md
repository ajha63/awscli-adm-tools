# AWS CLI Admin Tools

**AWS CLI Admin Tools** es un proyecto de scripts orientado a facilitar la gestión de actividades cotidianas para el mantenimiento de infraestructuras en AWS. El propósito es desarrollar y mejorar continuamente herramientas de línea de comandos que simplifiquen tareas operativas frecuentes, reduciendo el trabajo manual y los errores en la administración de recursos y servicios cloud.

Construido sobre Python 3.14 y boto3.

## Requisitos

- [uv](https://docs.astral.sh/uv/) ≥ 0.4
- AWS CLI configurado con IAM Identity Center (SSO)
- Perfil `johndoe` (o el que configures en `.env`)

## Configuración inicial

```bash
# 1. Clonar y entrar al directorio
cd aws-adm-script

# 2. Crear .env a partir del ejemplo
cp .env.example .env
# Edita .env con tus valores (perfil, región, account ID)

# 3. Instalar dependencias (crea .venv automáticamente)
uv sync

# 4. Autenticarte con SSO
aws sso login --profile johndoe
```

## Uso de scripts

```bash
# Listar instancias EC2 (todas las regiones)
uv run python -m aws_adm_script.ec2.list_instances --region us-east-1

# Solo instancias en ejecución
uv run python -m aws_adm_script.ec2.list_instances --state running

# Listar buckets S3
uv run python -m aws_adm_script.s3.list_buckets

# Listar roles IAM
uv run python -m aws_adm_script.iam.list_roles

# Filtrar roles por path prefix
uv run python -m aws_adm_script.iam.list_roles --prefix /aws-reserved/
```

## Scripts disponibles

Catálogo de scripts desarrollados. Actualizar esta sección cada vez que se agregue, modifique o deprece un script.

### EC2

| Script | Módulo | Descripción | Parámetros principales |
|--------|--------|-------------|------------------------|
| Listar instancias | `aws_adm_script.ec2.list_instances` | Lista instancias EC2 en una región con Id, Name, State, Type y LaunchTime | `--region`, `--state`, `--profile` |
| Consultar capacidad | `aws_adm_script.ec2.consulta_capacidad_ec2` | Consulta la capacidad de una familia o tipo de instancia EC2 y realiza una verificación de capacidad real forzando una solicitud con DRY RUN por zona de disponibilidad. | `--tipoEC2`, `--region`, `--formato`, `--verificar-capacidad`, `--profile` |

---

#### `consulta_capacidad_ec2` — Detalle

**Propósito**

Consulta la capacidad de una familia de instancias (ej. `m5`) o un tipo exacto (ej. `m5.large`) y realiza una verificación de capacidad real forzando una solicitud con DRY RUN en cada zona de disponibilidad. El dry-run le indica a AWS que procese la solicitud completa sin materializar el recurso, lo que permite determinar si hay capacidad disponible en una zona antes de comprometerse con una reserva real.

El script obtiene para cada tipo consultado:

- Especificaciones técnicas: vCPUs, memoria (MiB), arquitecturas soportadas, rendimiento de red y almacenamiento local.
- Zonas de disponibilidad donde el tipo está disponible en la región indicada.
- Capacidad real disponible por zona (opcional), usando un dry-run de `create_capacity_reservation` que no crea ningún recurso en la cuenta.

**Parámetros**

| Parámetro | Obligatorio | Valores | Descripción |
|-----------|-------------|---------|-------------|
| `--tipoEC2` | ✅ | familia (`m5`) o tipo exacto (`m5.large`) | Familia o tipo de instancia a consultar |
| `--region` | No | código de región (default: `us-east-1`) | Región AWS donde se realiza la consulta |
| `--formato` | No | `json` (default) · `yaml` | Formato de la salida estándar |
| `--verificar-capacidad` | No | flag (sin valor) | Activa el dry-run por zona para verificar capacidad real |
| `--profile` | No | nombre de perfil AWS CLI | Perfil IAM Identity Center a usar |

**Permisos IAM mínimos requeridos**

```
ec2:DescribeInstanceTypes
ec2:DescribeInstanceTypeOfferings
ec2:CreateCapacityReservation   ← solo si se usa --verificar-capacidad
```

**Ejemplos de uso**

```bash
# Consultar todos los tipos de la familia m5 en us-east-1 (salida JSON)
uv run python -m aws_adm_script.ec2.consulta_capacidad_ec2 \
    --region us-east-1 --tipoEC2 m5

# Tipo exacto en otra región, salida YAML
uv run python -m aws_adm_script.ec2.consulta_capacidad_ec2 \
    --region eu-west-1 --tipoEC2 t3.medium --formato yaml

# Verificar capacidad real por zona (dry-run, no crea recursos)
uv run python -m aws_adm_script.ec2.consulta_capacidad_ec2 \
    --region us-east-1 --tipoEC2 c5.xlarge --verificar-capacidad

# Con perfil SSO explícito y salida YAML
uv run python -m aws_adm_script.ec2.consulta_capacidad_ec2 \
    --profile johndoe --region us-east-1 --tipoEC2 m5.large \
    --formato yaml --verificar-capacidad
```

**Formato de resultado**

La salida es un objeto con la siguiente estructura (JSON por defecto, convertible a YAML con `--formato yaml`):

```json
{
  "region": "us-east-1",
  "tipoEC2_consultado": "m5",
  "total_tipos": 2,
  "tipos": [
    {
      "tipo": "m5.large",
      "especificaciones": {
        "vCPUs": 2,
        "MemoriaMiB": 8192,
        "Arquitecturas": ["x86_64"],
        "RedGbps": "Up to 10 Gigabit",
        "Almacenamiento": null
      },
      "zonas_disponibles": ["us-east-1a", "us-east-1b", "us-east-1c"],
      "total_zonas": 3,
      "capacidad_por_zona": {
        "us-east-1a": "disponible",
        "us-east-1b": "disponible",
        "us-east-1c": "sin_capacidad"
      }
    }
  ]
}
```

> El campo `capacidad_por_zona` solo aparece cuando se usa `--verificar-capacidad`.
> Los valores posibles son `disponible`, `sin_capacidad` o `error: <código>`.

El mismo resultado en formato YAML (`--formato yaml`):

```yaml
region: us-east-1
tipoEC2_consultado: m5
total_tipos: 2
tipos:
- tipo: m5.large
  especificaciones:
    vCPUs: 2
    MemoriaMiB: 8192
    Arquitecturas:
    - x86_64
    RedGbps: Up to 10 Gigabit
    Almacenamiento: null
  zonas_disponibles:
  - us-east-1a
  - us-east-1b
  - us-east-1c
  total_zonas: 3
  capacidad_por_zona:
    us-east-1a: disponible
    us-east-1b: disponible
    us-east-1c: sin_capacidad
```

### S3

| Script | Módulo | Descripción | Parámetros principales |
|--------|--------|-------------|------------------------|
| Listar buckets | `aws_adm_script.s3.list_buckets` | Lista todos los buckets S3 con región, estado de versionado y fecha de creación | `--region`, `--profile` |

### IAM

| Script | Módulo | Descripción | Parámetros principales |
|--------|--------|-------------|------------------------|
| Listar roles | `aws_adm_script.iam.list_roles` | Lista roles IAM con RoleName, RoleId, Path y CreateDate | `--prefix`, `--region`, `--profile` |

### Lambda

> _Sin scripts aún — módulo reservado._

### RDS

> _Sin scripts aún — módulo reservado._

---

## Desarrollo

```bash
# Ejecutar linter
uv run ruff check src/

# Formatear código
uv run ruff format src/

# Type checking
uv run mypy src/

# Tests
uv run pytest
```

## Estructura

```
aws-adm-script/
├── src/aws_adm_script/
│   ├── ec2/            # Scripts EC2
│   ├── s3/             # Scripts S3
│   ├── iam/            # Scripts IAM
│   ├── lambda_fn/      # Scripts Lambda
│   ├── rds/            # Scripts RDS
│   └── utils/          # Sesión boto3, helpers
├── scripts/            # Entry points CLI ejecutables
├── tests/              # Pruebas pytest
├── config/             # Configuración y settings
├── .env.example        # Plantilla de variables de entorno
└── pyproject.toml      # Dependencias y herramientas
```

## Seguridad

- Las credenciales AWS se gestionan exclusivamente vía **IAM Identity Center / SSO**.
- Nunca se almacenan `AWS_ACCESS_KEY_ID` ni `AWS_SECRET_ACCESS_KEY` en el repositorio.
- El archivo `.env` está en `.gitignore` — solo `.env.example` se versiona.
- Cada script verifica la identidad activa antes de ejecutar operaciones.
