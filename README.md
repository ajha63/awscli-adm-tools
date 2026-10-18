# AWS CLI Admin Tools

**AWS CLI Admin Tools** es un proyecto de scripts orientado a facilitar la gestión de actividades cotidianas para el mantenimiento de infraestructuras en AWS. El propósito es desarrollar y mejorar continuamente herramientas de línea de comandos que simplifiquen tareas operativas frecuentes, reduciendo el trabajo manual y los errores en la administración de recursos y servicios cloud.

Construido sobre Python 3.14 y boto3.

## Requisitos

- [uv](https://docs.astral.sh/uv/) ≥ 0.4
- AWS CLI configurado con IAM Identity Center (SSO)
- Perfil `alhernan` (o el que configures en `.env`)

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
aws sso login --profile alhernan
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
