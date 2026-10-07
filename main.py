import typer
from rich.console import Console
from rich.table import Table
from datetime import datetime
import db
from cli_interactiva import menu_principal

app = typer.Typer(help="Control mensual de pagos recurrentes.")
console = Console()

@app.callback()
def setup():
    db.init_db()

@app.command("servicio-nuevo")
def nuevo_servicio(
    nombre: str, 
    monto_estimado: float = typer.Argument(0.0, help="Monto estimado mensual")
):
    """
    Agrega un servicio recurrente a la plantilla.
    Ejemplo: python main.py servicio-nuevo "Internet" 25000
    """
    try:
        db.agregar_servicio(nombre, monto_estimado)
        console.print(f"[bold green]✓[/bold green] Servicio '[bold]{nombre}[/bold]' agregado a la lista recurrente.")
    except Exception:
        console.print(f"[bold red]✗[/bold red] El servicio '[bold]{nombre}[/bold]' ya existe.")

@app.command("servicios")
def listar_servicios():
    """Muestra la plantilla general de servicios recurrentes."""
    servicios = db.obtener_servicios()
    if not servicios:
        console.print("[yellow]No hay servicios registrados. Agrega uno con 'servicio-nuevo'.[/yellow]")
        return

    table = Table(title="Plantilla de Servicios Recurrentes")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Servicio", style="bold")
    table.add_column("Monto Est.", justify="right")

    for s_id, nombre, monto in servicios:
        table.add_row(str(s_id), nombre, f"${monto:,.2f}")

    console.print(table)

@app.command("mes")
def ver_mes(
    periodo: str = typer.Option(
        None, 
        "--periodo", "-p", 
        help="Periodo en formato YYYY-MM (por defecto el mes actual)"
    )
):
    """
    Muestra la lista con checkboxes para un mes determinado.
    Ejemplo: python main.py mes -p 2026-10
    """
    if not periodo:
        periodo = datetime.now().strftime("%Y-%m")

    pagos = db.obtener_pagos_mes(periodo)

    if not pagos:
        console.print(f"[yellow]No hay servicios configurados para el mes {periodo}.[/yellow]")
        return

    table = Table(title=f"Estado de Pagos: {periodo}")
    table.add_column("Check", justify="center")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Servicio", style="bold")
    table.add_column("Monto", justify="right")
    table.add_column("Estado", justify="center")

    total_mes = 0.0
    total_pagado = 0.0

    for pago_id, servicio, monto, pagado in pagos:
        total_mes += monto
        if pagado:
            total_pagado += monto
            checkbox = "[bold green][x][/bold green]"
            estado_txt = "[green]PAGADO[/green]"
        else:
            checkbox = "[bold red][ ][/bold red]"
            estado_txt = "[red]PENDIENTE[/red]"

        table.add_row(
            checkbox,
            str(pago_id),
            servicio,
            f"${monto:,.2f}",
            estado_txt
        )

    console.print(table)
    console.print(f"Progreso: [green]${total_pagado:,.2f}[/green] de [bold]${total_mes:,.2f}[/bold]\n")

@app.command("check")
def marcar_desmarcar(pago_id: int, periodo: str = None):
    """
    Alterna el estado (checkbox) de un pago usando su ID.
    Ejemplo: python main.py check 2
    """
    exito = db.toggle_pago(pago_id)
    if exito:
        console.print(f"[bold green]✓[/bold green] Estado del pago ID [bold]{pago_id}[/bold] actualizado.")
        # Muestra la tabla actualizada del mes correspondiente
        if not periodo:
            periodo = datetime.now().strftime("%Y-%m")
        ver_mes(periodo)
    else:
        console.print(f"[bold red]✗[/bold red] No se encontró el registro con ID {pago_id}.")

@app.command("servicio-eliminar")
def borrar_servicio(servicio_id: int):
    """
    Elimina un servicio de la plantilla y sus registros históricos.
    Ejemplo: python main.py servicio-eliminar 1
    """
    exito = db.eliminar_servicio(servicio_id)
    if exito:
        console.print(f"[bold green]✓[/bold green] El servicio ID [bold]{servicio_id}[/bold] y su historial fueron eliminados.")
    else:
        console.print(f"[bold red]✗[/bold red] No se encontró ningún servicio con el ID {servicio_id}.")

if __name__ == "__main__":
    menu_principal()