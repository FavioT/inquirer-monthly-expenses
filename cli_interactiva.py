from datetime import datetime
import math
import sqlite3

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
import db
from formato import formatear_monto

console = Console()


def _barra_progreso(completados: int, total: int, ancho: int = 20) -> Text:
    porcentaje = completados / total if total else 0
    bloques = round(porcentaje * ancho)
    barra = Text("█" * bloques, style="green")
    barra.append("░" * (ancho - bloques), style="bright_black")
    barra.append(f"  {porcentaje:.0%} ({completados}/{total})", style="bold")
    return barra


def _mostrar_encabezado(periodo: str) -> None:
    console.print(
        Panel(
            f"[bold]Controla tus servicios y pagos recurrentes[/bold]\n"
            f"[dim]Período actual: {periodo}[/dim]",
            title="[bold cyan]GESTOR DE PAGOS[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def gestionar_mes(periodo: str):
    """Pantalla interactiva de checklist de pagos para un mes específico."""
    pagos = db.obtener_pagos_mes(periodo)

    if not pagos:
        console.print(
            Panel(
                "Todavía no hay servicios para mostrar. Agrega uno desde el menú principal.",
                title="[yellow]Checklist vacío[/yellow]",
                border_style="yellow",
            )
        )
        return

    choices = [
        Choice(
            value=pago_id,
            name=f"{servicio}  •  {formatear_monto(monto)}",
            enabled=bool(pagado)
        )
        for pago_id, servicio, monto, pagado in pagos
    ]

    cantidad_pagada = sum(bool(pagado) for _, _, _, pagado in pagos)
    total_mes = sum(monto for _, _, monto, _ in pagos)
    total_pagado = sum(monto for _, _, monto, pagado in pagos if pagado)
    resumen = Table.grid(padding=(0, 2))
    resumen.add_row("Avance", _barra_progreso(cantidad_pagada, len(pagos)))
    resumen.add_row("Pagado", Text(formatear_monto(total_pagado), style="green"))
    resumen.add_row("Por pagar", Text(formatear_monto(total_mes - total_pagado), style="yellow"))
    console.print(
        Panel(
            resumen,
            title=f"[bold cyan]PAGOS DE {periodo}[/bold cyan]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print(
        "[dim]↑/↓ navegar  •  Espacio marcar o desmarcar  •  Enter guardar[/dim]\n"
    )

    seleccionados = inquirer.checkbox(
        message="Marca los servicios que ya pagaste:",
        choices=choices,
        pointer="❯",
        enabled_symbol="[x] ",
        disabled_symbol="[ ] ",
        instruction="Espacio cambia el estado"
    ).execute()

    db.guardar_estado_pagos(periodo, set(seleccionados))
    pagos_actualizados = db.obtener_pagos_mes(periodo)
    cantidad_actualizada = sum(bool(pagado) for _, _, _, pagado in pagos_actualizados)
    console.print(
        Panel(
            _barra_progreso(cantidad_actualizada, len(pagos_actualizados)),
            title="[bold green]Cambios guardados[/bold green]",
            border_style="green",
        )
    )


def agregar_servicio_prompt():
    """Formulario interactivo para crear un nuevo servicio."""
    nombre = inquirer.text(
        message="Nombre del servicio (ej: Luz, Internet):",
        validate=lambda val: len(val.strip()) > 0 or "El nombre no puede estar vacío."
    ).execute().strip()

    monto_str = inquirer.text(
        message="Monto estimado mensual ($):",
        default="0.0",
        validate=lambda val: _monto_valido(val) or "Ingresa un monto finito mayor o igual a cero."
    ).execute()

    monto = float(monto_str)
    try:
        db.agregar_servicio(nombre, monto)
        console.print(f"\n[bold green]✓ Servicio '{nombre}' agregado exitosamente.[/bold green]\n")
    except sqlite3.IntegrityError:
        console.print(f"\n[bold red]✗ El servicio '{nombre}' ya existe.[/bold red]\n")


def _monto_valido(valor: str) -> bool:
    try:
        monto = float(valor)
    except ValueError:
        return False
    return math.isfinite(monto) and monto >= 0


def eliminar_servicio_prompt():
    """Selección interactiva para eliminar un servicio."""
    servicios = db.obtener_servicios()
    if not servicios:
        console.print("\n[yellow]No hay servicios para eliminar.[/yellow]\n")
        return

    choices = [
        Choice(value=s_id, name=f"{nombre} ({formatear_monto(monto)})")
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
            if db.eliminar_servicio(s_id_eliminar):
                console.print("\n[bold green]✓ Servicio e historial eliminados.[/bold green]\n")
            else:
                console.print("\n[yellow]El servicio ya no estaba disponible.[/yellow]\n")


def mostrar_servicios():
    """Muestra la plantilla de servicios recurrentes."""
    servicios = db.obtener_servicios()
    if not servicios:
        console.print(
            Panel(
                "No hay servicios registrados. Agrega uno para empezar.",
                title="[yellow]Sin servicios[/yellow]",
                border_style="yellow",
            )
        )
        return

    tabla = Table(
        title="Servicios recurrentes",
        header_style="bold cyan",
        border_style="blue",
        show_lines=True,
    )
    tabla.add_column("Servicio", style="bold")
    tabla.add_column("Monto mensual", justify="right", style="green")

    for _, nombre, monto in servicios:
        tabla.add_row(nombre, formatear_monto(monto))

    total_estimado = sum(monto for _, _, monto in servicios)
    tabla.add_section()
    tabla.add_row(Text(f"{len(servicios)} servicios", style="dim"), Text(formatear_monto(total_estimado), style="bold cyan"))
    console.print(tabla)


def mostrar_reporte_mes(periodo: str):
    """Muestra un resumen detallado con los gastos pagados vs no pagados del mes."""
    pagados, pendientes = db.obtener_resumen_mes(periodo)

    if not pagados and not pendientes:
        console.print(
            Panel(
                "No hay servicios configurados para este período.",
                title=f"[yellow]REPORTE {periodo}[/yellow]",
                border_style="yellow",
            )
        )
        inquirer.text(message="Presiona Enter para volver al menú...").execute()
        return

    total_pagado = sum(monto for _, monto in pagados)
    total_pendiente = sum(monto for _, monto in pendientes)
    total_general = total_pagado + total_pendiente

    tabla = Table(
        title=f"Resumen financiero · {periodo}",
        header_style="bold cyan",
        border_style="blue",
        show_lines=True,
    )
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Servicio", style="bold")
    tabla.add_column("Monto", justify="right")
    for servicio, monto in pagados:
        tabla.add_row(Text("PAGADO", style="green"), servicio, Text(formatear_monto(monto), style="green"))
    for servicio, monto in pendientes:
        tabla.add_row(Text("PENDIENTE", style="yellow"), servicio, Text(formatear_monto(monto), style="yellow"))

    console.print(
        Panel(
            tabla,
            title=f"[bold cyan]REPORTE FINANCIERO · {periodo}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    progreso = Table.grid(padding=(0, 2))
    progreso.add_row("Servicios pagados", _barra_progreso(len(pagados), len(pagados) + len(pendientes)))
    progreso.add_row("Total pagado", Text(formatear_monto(total_pagado), style="green"))
    progreso.add_row("Total pendiente", Text(formatear_monto(total_pendiente), style="yellow"))
    progreso.add_row("Total del mes", Text(formatear_monto(total_general), style="bold cyan"))
    console.print(Panel(progreso, title="Totales", border_style="blue", expand=False))
    
    inquirer.text(message="Presiona Enter para volver al menú...").execute()


def menu_principal():
    """Bucle del menú interactivo principal."""
    db.init_db()

    while True:
        periodo_actual = datetime.now().strftime("%Y-%m")
        console.print()
        _mostrar_encabezado(periodo_actual)

        opcion = inquirer.select(
            message="Menú principal · elige una opción:",
            choices=[
                Choice(value="mes_actual", name="✓  Marcar pagos del mes actual"),
                Choice(value="reporte_actual", name="▤  Ver reporte financiero del mes"),
                Choice(value="otro_mes", name="◷  Consultar pagos de otro mes"),
                Choice(value="ver_servicios", name="▦  Ver servicios recurrentes"),
                Choice(value="nuevo_servicio", name="＋  Agregar un servicio"),
                Choice(value="eliminar_servicio", name="−  Eliminar un servicio"),
                Choice(value="salir", name="Salir")
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
                default=periodo_actual,
                validate=lambda valor: db.es_periodo_valido(valor) or "Ingresa un mes válido en formato YYYY-MM."
            ).execute().strip()
            gestionar_mes(mes_custom)
        elif opcion == "ver_servicios":
            mostrar_servicios()
        elif opcion == "nuevo_servicio":
            agregar_servicio_prompt()
        elif opcion == "eliminar_servicio":
            eliminar_servicio_prompt()
        elif opcion == "salir":
            console.print("[bold cyan]¡Hasta luego![/bold cyan]")
            break