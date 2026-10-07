# Gestor de Pagos Mensuales

Aplicación de terminal para registrar servicios recurrentes, marcar pagos por mes y consultar reportes. Los datos se guardan localmente en SQLite (`pagos.db`).

## Requisitos

- Python 3.8 o superior.

## Instalación

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requisitos.txt
```

## Uso

Inicia el menú interactivo:

```powershell
py main.py
```

También puedes usar los comandos:

```powershell
py main.py --help
py main.py servicio-nuevo "Internet" 25000
py main.py servicios
py main.py mes --periodo 2026-10
py main.py check 1
py main.py servicio-eliminar 1
```

Los períodos deben usar el formato `YYYY-MM`, con un mes entre `01` y `12`. El monto estimado debe ser un número finito mayor o igual a cero.
