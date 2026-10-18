# Historial de construccion: `consultar_capacidad_ec2.py`

Este documento describe, paso a paso, las instrucciones usadas para generar y
evolucionar el script `scripts/consultar_capacidad_ec2.py`, junto con las acciones
realizadas y los artefactos resultantes en el proyecto `kiroadmscripts`.

---

## Paso 1 — Crear el script inicial

**Instruccion:**
> usando sdk y python elabora un script que reciba los parametros region y
> tipoEC2 para consultar la capacidad de una familia de instancias

**Que se hizo:**
- Se creo `consultar_capacidad_ec2.py` usando **boto3** (AWS SDK para Python).
- El script recibe `--region` y `--tipoEC2` (tipo exacto como `m5.large` o familia
  completa como `m5`).
- Consulta realizada con las APIs de EC2:
  - `describe_instance_types` -> especificaciones (vCPUs, memoria, red, arquitecturas).
  - `describe_instance_type_offerings` -> zonas de disponibilidad donde se ofrece el tipo.
  - Opcion `--verificar-capacidad`: dry-run de `create_capacity_reservation` para
    comprobar capacidad real por zona, sin crear recursos.
- Se agrego `--profile` para seleccionar un perfil de AWS.
- Las credenciales se resuelven desde el entorno / perfil / rol (nunca embebidas).

**Artefactos:** `consultar_capacidad_ec2.py`, `requirements.txt`, `README.md`.

---

## Paso 2 — Crear un entorno de desarrollo aislado con uv

**Instruccion:**
> usando uv crea un ambiente de desarrollo aislado y estable para desarrollar
> scripts de proposito administrativo en cuentas AWS usando python 3.14, boto3 y sdk

**Que se hizo:**
- Se inicializo el proyecto con `uv init` fijando **Python 3.14**.
- Se definieron dependencias en `pyproject.toml`: `boto3` (ejecucion) y un grupo
  `dev` (ruff, mypy, pytest, stubs de tipos de boto3).
- Se genero el entorno aislado `.venv/` y el lockfile `uv.lock` con `uv sync`.
- El script se movio a `scripts/consultar_capacidad_ec2.py`.

**Comandos clave:**
```bash
uv init --name kiroadmscripts --python 3.14
uv sync
uv run python scripts/consultar_capacidad_ec2.py --help
```

---

## Paso 3 — Restriccion de seguridad: sin credenciales en el codigo

**Instruccion:**
> agregar una restriccion de seguridad que impida dejar credenciales en scripts
> o archivos de configuracion

**Que se hizo (controles en varias capas):**
- `security/secret_scanner.py`: escaner de credenciales (AWS Access Keys, secret
  keys, session tokens, claves PEM, contraseñas, tokens, URLs con credenciales).
- `.githooks/pre-commit`: hook de git que bloquea commits con secretos
  (`git config core.hooksPath .githooks`).
- `.gitignore` reforzado para no versionar `.env`, `credentials`, `*.pem`, etc.
- `.kiro/hooks/no-credentials-in-files.json`: hook de Kiro (`PreToolUse`) que
  verifica el contenido antes de escribir archivos.
- `.kiro/steering/security.md`: politica permanente del proyecto.

---

## Paso 4 — Regla de flujo: status check del repositorio

**Instruccion:**
> agrega una regla que obligue un status check del repositorio cada vez que el
> desarrollador pida iniciar la creacion de un nuevo script o investigacion de un
> script existente y emite una alerta para que ejecute las tareas pendientes

**Que se hizo:**
- `security/repo_status_check.sh`: verifica cambios sin commitear, archivos sin
  seguimiento y commits sin publicar; emite `ALERTA_REPO` o `ESTADO_REPO: Limpio`.
- `security/prompt_status_gate.sh`: wrapper que detecta por palabras clave si el
  prompt pide crear/investigar un script.
- `.kiro/hooks/repo-status-on-script-work.json`: hook de Kiro (`UserPromptSubmit`).
- `.kiro/steering/repo-status.md`: regla documentada.

---

## Paso 5 — Regla de documentacion de scripts en README

**Instruccion:**
> para cada script administrativo desarrollado agrega una entrada en README.md
> que describa el objetivo de la funcion y ejemplo de uso

**Que se hizo:**
- Se reestructuro la seccion "Scripts administrativos" del README con el formato
  **Objetivo / Parametros / Ejemplo de uso / Permisos IAM**.
- `.kiro/steering/documentacion-scripts.md`: regla + plantilla para que todo
  script nuevo se documente en el mismo cambio.

---

## Paso 6 — Preparar el ambiente para una mejora

**Instruccion:**
> prepara el ambiente de trabajo para una mejora del script consultar_capacidad_ec2.py

**Que se hizo:**
- Se committearon los cambios pendientes para dejar `main` limpio.
- Se creo la rama `feature/mejora-consultar-capacidad-ec2`.
- Se verifico el entorno `uv` (Python 3.14.7, boto3) y el baseline del script.

---

## Paso 7 — Agregar el parametro de formato de salida

**Instruccion:**
> añade al script un parametro para indicar cual sera el formato de salida del
> resultado, por defecto el formato de salida es json pero puede entregar
> resultado en formato yaml

**Que se hizo:**
- Se agrego `--formato` con valores `json` (por defecto) y `yaml`.
- Se refactorizo la salida: `construir_resultado()` arma una estructura de datos y
  `serializar()` la emite como JSON (`json.dumps`) o YAML (`yaml.safe_dump`).
- Se agrego la dependencia `pyyaml` con `uv add pyyaml`.
- Validacion: `ruff` limpio y round-trip JSON/YAML sobre datos simulados.

**Comando:**
```bash
uv add pyyaml
uv run python scripts/consultar_capacidad_ec2.py --region us-east-1 --tipoEC2 m5 --formato yaml
```

---

## Paso 8 — Documentar el efecto del nuevo parametro

**Instruccion:**
> Actualiza la documentacion del script consultar_capacidad_ec2.py en README.md
> señalando el parametro agregado, valores que puede tomar y el efecto que los
> parametro originan en la salida

**Que se hizo:**
- Se añadio al README la subseccion "Parametro agregado `--formato` (efecto en la
  salida)" con tabla de valores, descripcion de la estructura emitida y ejemplos
  de salida en JSON y YAML lado a lado.

---

## Paso 9 — Versionar la mejora y fusionar

**Instrucciones:**
> has git add y luego git commit con el mensaje "feature/se agrego formatos de salida de ejecucion"
> has la fusion de la rama con main
> elimina la rama, ya no sera necesaria

**Que se hizo:**
- `git add` + `git commit` de la mejora (el hook pre-commit escaneo sin secretos).
- `git merge` (fast-forward) de la rama de feature a `main`.
- `git branch -d` para eliminar la rama ya fusionada.

**Comandos:**
```bash
git add README.md pyproject.toml scripts/consultar_capacidad_ec2.py uv.lock
git commit -m "feature/se agrego formatos de salida de ejecucion"
git switch main
git merge feature/mejora-consultar-capacidad-ec2
git branch -d feature/mejora-consultar-capacidad-ec2
```

---

## Resultado final

El script `scripts/consultar_capacidad_ec2.py`:

- Recibe `--region`, `--tipoEC2`, `--formato` (json|yaml), `--verificar-capacidad`
  y `--profile`.
- Consulta especificaciones y disponibilidad por zona de una familia o tipo de EC2.
- Emite el resultado en JSON (por defecto) o YAML.
- Obtiene credenciales de forma segura (entorno / perfil / rol), nunca embebidas.

Todo integrado en `main`, con controles de seguridad y de flujo activos y la
documentacion del script en `README.md`.
