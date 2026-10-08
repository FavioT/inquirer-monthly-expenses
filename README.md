# Gestor de Pagos Mensuales

Aplicación de terminal para organizar servicios recurrentes, registrar pagos por mes y consultar el avance de los gastos. Los datos se guardan localmente en SQLite, en el archivo `pagos.db`.

## Funciones

- Administra una lista de servicios recurrentes con su monto mensual estimado.
- Modifica el nombre y monto de un servicio recurrente desde el próximo mes, conservando los períodos anteriores.
- Marca o desmarca pagos desde un checklist interactivo por mes.
- Consulta reportes con pagos realizados, pendientes y totales.
- Muestra el avance mensual y el total estimado de los servicios.
- Presenta los importes con punto para miles y coma para decimales; por ejemplo, `$150.000,00`.
- Mantiene el estado de pago separado para cada mes.

## Requisitos

- Python 3.8 o superior.
- Terminal compatible con menús interactivos.

## Instalación

Desde la carpeta del proyecto, crea y activa un entorno virtual e instala las dependencias:

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requisitos.txt
```

### macOS o Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requisitos.txt
```

## Uso interactivo

Inicia el menú:

```bash
python main.py
```

Desde el menú puedes marcar los pagos del mes actual o de otro período, ver reportes y servicios, agregar, modificar o eliminar servicios junto con su historial. Las modificaciones de un servicio recurrente se aplican desde el próximo mes; el monto y nombre de los meses anteriores se conservan.

En el checklist, usa las flechas para navegar, **Espacio** para marcar o desmarcar un pago y **Enter** para guardar.

## Comandos

Consulta todos los comandos disponibles:

```bash
python main.py --help
```

Ejemplos:

```bash
# Agregar un servicio con monto mensual estimado
python main.py servicio-nuevo "Internet" 25000

# Listar los servicios recurrentes
python main.py servicios

# Ver los pagos de un período (YYYY-MM)
python main.py mes --periodo 2026-10

# Alternar el estado de un pago por su ID
python main.py check 1

# Eliminar un servicio y sus registros históricos por ID
python main.py servicio-eliminar 1

# Modificar nombre y monto desde el próximo mes
python main.py servicio-editar 1 "Internet" 30000
```

Los períodos deben tener el formato `YYYY-MM`, con un mes entre `01` y `12`. Los montos deben ser números finitos mayores o iguales a cero.

## Datos y privacidad

La base de datos `pagos.db` se crea automáticamente junto a los archivos de la aplicación. No la compartas si contiene información personal; los archivos de base de datos están excluidos de Git mediante `.gitignore`.

## Pruebas

Ejecuta las pruebas incluidas con:

```bash
python -m unittest discover -s tests -v
```
