---
inclusion: always
---

# Reglas de Seguridad — Credenciales y Secretos

## Regla fundamental

**Nunca escribir, sugerir ni aceptar credenciales reales en ningún archivo del repositorio.**

Esto incluye, sin excepción:

- `AWS_ACCESS_KEY_ID` con valor real (patrón `AKIA...`)
- `AWS_SECRET_ACCESS_KEY` con valor real
- `AWS_SESSION_TOKEN` con valor real
- Contraseñas, tokens de API, JWTs, claves privadas PEM
- Cualquier valor secreto en archivos `.env`, `.yaml`, `.json`, `.toml`, `.py`

---

## Autenticación AWS

Este proyecto usa **exclusivamente IAM Identity Center (SSO)** con perfiles AWS CLI.

```python
# ✅ CORRECTO — perfil SSO, sin credenciales hardcodeadas
session = boto3.Session(profile_name="alhernan", region_name="us-east-1")

# ❌ INCORRECTO — nunca hacer esto
session = boto3.Session(
    aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
    aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
)
```

---

## Archivos de configuración

| Archivo | ¿Va al repo? | Regla |
|---|---|---|
| `.env.example` | ✅ Sí | Solo placeholders, NUNCA valores reales |
| `.env` | ❌ No | En `.gitignore`. Solo local |
| `credentials` | ❌ No | En `.gitignore` |
| `*.pem`, `*.key` | ❌ No | En `.gitignore` |
| `cdk.context.json` | ❌ No | Puede contener IDs de cuenta y recursos |

---

## Variables de entorno

Cuando se necesite configuración sensible:

1. Agregarla a `.env.example` con un placeholder claro:
   ```
   DATABASE_PASSWORD=<reemplazar-con-valor-real>
   ```
2. Documentar en README cómo obtener el valor.
3. Leer en código vía `os.environ.get()` o `python-dotenv`.
4. **Nunca** pasar el valor como argumento CLI en scripts de CI/CD visibles.

---

## Antes de cualquier operación destructiva en AWS

Siempre ejecutar y mostrar la salida de:

```bash
aws sts get-caller-identity --profile <perfil>
```

Verificar que `Account` coincida con `554982632606` antes de continuar.

---

## Hook de pre-commit

El proyecto incluye un escáner automático en `.githooks/pre-commit`.
Instalarlo después de clonar:

```bash
bash scripts/install-hooks.sh
```

Este hook bloquea commits que contengan:
- Access Keys AWS (`AKIA...`)
- Secret Access Keys
- Claves privadas PEM
- Tokens genéricos o contraseñas hardcodeadas
- Archivos `.env`, `credentials`, `*.pem`, `*.key`

---

## Si se expone una credencial accidentalmente

1. **Revocarla inmediatamente** en la consola AWS IAM o IAM Identity Center.
2. Limpiar el historial de git con `git filter-repo` o contactar al administrador.
3. Revisar CloudTrail para detectar uso no autorizado.
4. **No hacer `git push --force`** sin coordinar con el equipo.
