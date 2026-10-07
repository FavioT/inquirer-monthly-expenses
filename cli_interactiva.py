from datetime import datetime
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import db

console = Console()

def gestionar_mes(periodo: str):
    """Pantalla interactiva de checklist de pagos para un mes específico."""
    pagos = db.obtener_pagos_mes(periodo)

    if not pagos:
        console.print(f"\n[yellow]No hay servicios configurados. Agrega uno desde el menú principal.[/yellow]\n")
        return

    # Mapear los servicios a opciones de InquirerPy
    choices = [
        Choice(
            value=pago_id,
            name=f"{servicio:<20} | ${monto:,.2f}",
            enabled=bool(pagado)
        )
        for pago_id, servicio, monto, pagado in pagos
    ]

    console.print(f"\n[bold cyan]=== GESTIÓN DE PAGOS: {periodo} ===[/bold cyan]")
    console.print("[dim]Navega con las flechas ↑/↓ | Presiona [Espacio] para tildar/destildar | [Enter] para Guardar[/dim]\n")

    seleccionados = inquirer.checkbox(
        message="Selecciona los servicios pagados:",
        choices=choices,
        pointer="❯",
        enabled_symbol="[x] ",
        disabled_symbol="[ ] ",
        instruction="(Usa espacio para marcar)"
    ).execute()

    # Guardar cambios
    db.guardar_estado_pagos(periodo, set(seleccionados))
    console.print("\n[bold green]✓ ¡Cambios guardados correctamente![/bold green]\n")


def agregar_servicio_prompt():
    """Formulario interactivo para crear un nuevo servicio."""
    nombre = inquirer.text(
        message="Nombre del servicio (ej: Luz, Internet):",
        validate=lambda val: len(val.strip()) > 0 or "El nombre no puede estar vacío."
    ).execute().strip()

    monto_str = inquirer.text(
        message="Monto estimado mensual ($):",
        default="0.0",
        validate=lambda val: val.replace(".", "", 1).isdigit() or "Ingresa un número válido."
    ).execute()

    monto = float(monto_str)
    try:
        db.agregar_servicio(nombre, monto)
        console.print(f"\n[bold green]✓ Servicio '{nombre}' agregado exitosamente.[/bold green]\n")
    except Exception:
        console.print(f"\n[bold red]✗ El servicio '{nombre}' ya existe.[/bold red]\n")


def eliminar_servicio_prompt():
    """Selección interactiva para eliminar un servicio."""
    servicios = db.obtener_servicios()
    if not servicios:
        console.print("\n[yellow]No hay servicios para eliminar.[/yellow]\n")
        return

    choices = [
        Choice(value=s_id, name=f"{nombre} (${monto:,.2f})")
        for s_id, nombre, monto in servicios
    ]
    choices.append(Choice(value=None, name="← Cancelar"))

    s_id_eliminar = inquirer.select(
        message="Selecciona el servicio que deseas eliminar:",
        choices=choices
    ).execute()

    if s_id_eliminar:
        confirmar = inquirer.confirm(
            message="¿Seguro que deseas eliminar este servicio y su historial?",
            default=False
        ).execute()

        if confirmar:
            db.eliminar_servicio(s_id_eliminar)
            console.print("\n[bold green]✓ Servicio eliminado.[/bold green]\n")

def mostrar_reporte_mes(periodo: str):
    """Muestra un resumen detallado con los gastos pagados vs no pagados del mes."""
    pagados, pendientes = db.obtener_resumen_mes(periodo)

    total_pagado = sum(monto for _, monto in pagados)
    total_pendiente = sum(monto for _, monto in pendientes)
    total_general = total_pagado + total_pendiente

    console.print(f"\n[bold cyan]=== REPORTE FINANCIERO DE {periodo} ===[/bold cyan]\n")

    # Tabla 1: Gastos Pagados
    tabla_pagados = Table(title="[bold green]✓ Gastos Pagados[/bold green]", show_header=True)
    tabla_pagados.add_column("Servicio", style="bold")
    tabla_pagados.add_column("Monto", justify="right", style="green")

    for servicio, monto in pagados:
        tabla_pagados.add_row(servicio, f"${monto:,.2f}")

    if not pagados:
        tabla_pagados.add_row("[dim]Ningún pago realizado aún[/dim]", "$0.00")

    # Tabla 2: Gastos Pendientes
    tabla_pendientes = Table(title="[bold red]✗ Gastos No Pagados (Pendientes)[/bold red]", show_header=True)
    tabla_pendientes.add_column("Servicio", style="bold")
    tabla_pendientes.add_column("Monto", justify="right", style="red")

    for servicio, monto in pendientes:
        tabla_pendientes.add_row(servicio, f"${monto:,.2f}")

    if not pendientes:
        tabla_pendientes.add_row("[dim]¡Al día! No hay pendientes[/dim]", "$0.00")

    # Imprimir tablas
    console.print(tabla_pagados)
    console.print("")
    console.print(tabla_pendientes)
    console.print("")

    # Panel de Resumen
    resumen_text = (
        f"[bold]Total Pagado:[/bold]     [green]${total_pagado:,.2f}[/green]\n"
        f"[bold]Total Pendiente:[/bold]  [red]${total_pendiente:,.2f}[/red]\n"
        f"[bold]Total del Mes:[/bold]    [cyan]${total_general:,.2f}[/cyan]"
    )
    console.print(Panel(resumen_text, title="Totales del Mes", expand=False))
    
    inquirer.text(message="Presiona [Enter] para volver al menú principal...").execute()


def menu_principal():
    """Bucle del menú interactivo principal."""
    db.init_db()

    while True:
        periodo_actual = datetime.now().strftime("%Y-%m")

        opcion = inquirer.select(
            message="¿Qué deseas hacer?",
            choices=[
                Choice(value="mes_actual", name=f"1. Checkbox del mes actual ({periodo_actual})"),
                Choice(value="reporte_actual", name=f"2. Ver reporte de gastos del mes ({periodo_actual})"),
                Choice(value="otro_mes", name="3. Checkbox de otro mes (ej: 2026-11)"),
                Choice(value="nuevo_servicio", name="4. Agregar nuevo servicio a la lista"),
                Choice(value="eliminar_servicio", name="5. Eliminar servicio de la lista"),
                Choice(value="salir", name="6. Salir")
            ],
            pointer="❯"
        ).execute()

        if opcion == "mes_actual":
            gestionar_mes(periodo_actual)
        elif opcion == "reporte_actual":
            mostrar_reporte_mes(periodo_actual)
        elif opcion == "otro_mes":
            mes_custom = inquirer.text(
                message="Ingresa el período (YYYY-MM):",
                default=periodo_actual
            ).execute().strip()
            gestionar_mes(mes_custom)
        elif opcion == "nuevo_servicio":
            agregar_servicio_prompt()
        elif opcion == "eliminar_servicio":
            eliminar_servicio_prompt()
        elif opcion == "salir":
            console.print("[bold cyan]¡Hasta luego![/bold cyan]")
            break