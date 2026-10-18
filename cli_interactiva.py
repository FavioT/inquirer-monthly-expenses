from datetime import datetime
import sqlite3
from typing import Optional, Union

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from rich.console import Console, Group
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
import db
from formato import (
    ICONO_AVISO,
    ICONO_ERROR,
    ICONO_OK,
    PUNTERO,
    es_monto_valido,
    formatear_monto,
    monto_editable,
    nombre_periodo,
    parsear_monto,
)

console = Console()

# Esc cancela cualquier formulario y devuelve None.
CANCELABLE = {"mandatory": False, "keybindings": {"skip": [{"key": "escape"}]}}
AYUDA_CANCELAR = "Esc para cancelar"


def _periodo_actual() -> str:
    return datetime.now().strftime("%Y-%m")


def _exito(mensaje: str) -> str:
    return f"[bold green]{ICONO_OK} {mensaje}[/bold green]"


def _error(mensaje: str) -> str:
    return f"[bold red]{ICONO_ERROR} {mensaje}[/bold red]"


def _aviso(mensaje: str) -> str:
    return f"[yellow]{ICONO_AVISO} {mensaje}[/yellow]"


def _pausa() -> None:
    inquirer.text(message="Presiona Enter para volver...", qmark="", amark="").execute()


def _barra_progreso(completados: int, total: int, ancho: int = 20) -> Text:
    porcentaje = completados / total if total else 0
    bloques = round(porcentaje * ancho)
    barra = Text("█" * bloques, style="green")
    barra.append("░" * (ancho - bloques), style="bright_black")
    barra.append(f"  {porcentaje:.0%} ({completados}/{total})", style="bold")
    return barra


def _resumen_mes(pagos) -> Table:
    cantidad_pagada = sum(bool(pagado) for _, _, _, pagado in pagos)
    total_mes = sum(monto for _, _, monto, _ in pagos)
    total_pagado = sum(monto for _, _, monto, pagado in pagos if pagado)
    resumen = Table.grid(padding=(0, 2))
    resumen.add_row("Avance", _barra_progreso(cantidad_pagada, len(pagos)))
    resumen.add_row("Pagado", Text(formatear_monto(total_pagado), style="green"))
    resumen.add_row("Por pagar", Text(formatear_monto(total_mes - total_pagado), style="yellow"))
    resumen.add_row("Total del mes", Text(formatear_monto(total_mes), style="bold cyan"))
    return resumen


def _mostrar_encabezado(periodo: str, aviso: Optional[str] = None) -> None:
    pagos = db.obtener_pagos_mes(periodo)
    contenido = [Text(f"Período actual: {nombre_periodo(periodo)}", style="dim"), Text()]
    if pagos:
        contenido.append(_resumen_mes(pagos))
        pendientes = [servicio for _, servicio, _, pagado in pagos if not pagado]
        contenido.append(Text())
        if pendientes:
            contenido.append(Text.assemble(("Pendientes: ", "yellow"), ", ".join(pendientes)))
        else:
            contenido.append(Text(f"{ICONO_OK} Todo pagado este mes", style="bold green"))
    else:
        contenido.append(Text("Todavía no hay servicios. Empieza agregando uno.", style="yellow"))

    console.print(
        Panel(
            Group(*contenido),
            title="[bold cyan]GESTOR DE PAGOS[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    if aviso:
        console.print(aviso)
    console.print()


def _elegir_servicio(mensaje: str):
    """Pide elegir un servicio; devuelve (id, nombre, monto) o None si se cancela."""
    servicios = db.obtener_servicios()
    if not servicios:
        return None

    ancho = max(len(nombre) for _, nombre, _ in servicios)
    choices = [
        Choice(value=servicio, name=f"{servicio[1]:<{ancho}}  {formatear_monto(servicio[2])}")
        for servicio in servicios
    ]
    choices.append(Separator("──────────────────────"))
    choices.append(Choice(value=None, name="← Cancelar"))

    return inquirer.select(
        message=mensaje,
        choices=choices,
        pointer=PUNTERO,
        long_instruction=AYUDA_CANCELAR,
        **CANCELABLE,
    ).execute()


def _pedir_monto(mensaje: str, default: str = "") -> Optional[float]:
    texto = inquirer.text(
        message=mensaje,
        default=default,
        validate=lambda val: es_monto_valido(val) or "Ingresa un monto válido, por ejemplo 25000 o 25.000,50.",
        transformer=lambda val: formatear_monto(parsear_monto(val)) if es_monto_valido(val) else val,
        long_instruction="Acepta 25000, 25.000 o 25.000,50  •  " + AYUDA_CANCELAR,
        **CANCELABLE,
    ).execute()
    return None if texto is None else parsear_monto(texto)


def _validar_nombre(valor: str, nombres_existentes: set) -> Union[bool, str]:
    nombre = valor.strip()
    if not nombre:
        return "El nombre no puede estar vacío."
    if nombre.casefold() in nombres_existentes:
        return f"Ya existe un servicio llamado '{nombre}'."
    return True


def gestionar_mes(periodo: str) -> Optional[str]:
    """Checklist interactivo de pagos de un mes. Devuelve un mensaje para mostrar."""
    pagos = db.obtener_pagos_mes(periodo)
    if not pagos:
        return _aviso("Todavía no hay servicios para mostrar. Agrega uno desde el menú principal.")

    console.print(
        Panel(
            _resumen_mes(pagos),
            title=f"[bold cyan]PAGOS DE {nombre_periodo(periodo).upper()}[/bold cyan]",
            border_style="cyan",
            padding=(0, 2),
        )
    )

    ancho = max(len(servicio) for _, servicio, _, _ in pagos)
    choices = [
        Choice(
            value=pago_id,
            name=f"{servicio:<{ancho}}  {formatear_monto(monto):>15}",
            enabled=bool(pagado),
        )
        for pago_id, servicio, monto, pagado in pagos
    ]

    seleccionados = inquirer.checkbox(
        message="Marca los servicios que ya pagaste:",
        choices=choices,
        pointer=PUNTERO,
        enabled_symbol="[x] ",
        disabled_symbol="[ ] ",
        instruction="",
        long_instruction=(
            "↑/↓ moverse  •  Espacio marcar  •  Ctrl+A marcar todos  •  "
            "Ctrl+R invertir  •  Enter guardar  •  Esc cancelar"
        ),
        transformer=lambda resultado: f"{len(resultado)} de {len(pagos)} pagados",
        **CANCELABLE,
    ).execute()

    if seleccionados is None:
        return _aviso("Cambios descartados.")

    antes = {pago_id for pago_id, _, _, pagado in pagos if pagado}
    despues = set(seleccionados)
    if antes == despues:
        return _aviso(f"Sin cambios en {nombre_periodo(periodo)}.")

    db.guardar_estado_pagos(periodo, despues)
    nombres = {pago_id: servicio for pago_id, servicio, _, _ in pagos}
    partes = []
    if despues - antes:
        partes.append("pagado: " + ", ".join(sorted(nombres[i] for i in despues - antes)))
    if antes - despues:
        partes.append("pendiente: " + ", ".join(sorted(nombres[i] for i in antes - despues)))
    return _exito(f"{nombre_periodo(periodo)} actualizado ({'; '.join(partes)}).")


def agregar_servicio_prompt() -> Optional[str]:
    """Formulario interactivo para crear un nuevo servicio."""
    existentes = {nombre.casefold() for _, nombre, _ in db.obtener_servicios()}
    nombre = inquirer.text(
        message="Nombre del servicio (ej: Luz, Internet):",
        validate=lambda val: _validar_nombre(val, existentes),
        long_instruction=AYUDA_CANCELAR,
        **CANCELABLE,
    ).execute()
    if nombre is None:
        return _aviso("Alta cancelada.")
    nombre = nombre.strip()

    monto = _pedir_monto("Monto mensual estimado ($):")
    if monto is None:
        return _aviso("Alta cancelada.")

    try:
        db.agregar_servicio(nombre, monto)
    except sqlite3.IntegrityError:
        return _error(f"El servicio '{nombre}' ya existe.")
    return _exito(f"Servicio '{nombre}' agregado ({formatear_monto(monto)} por mes).")


def eliminar_servicio_prompt() -> Optional[str]:
    """Selección interactiva para eliminar un servicio."""
    if not db.obtener_servicios():
        return _aviso("No hay servicios para eliminar.")

    servicio = _elegir_servicio("Selecciona el servicio que deseas eliminar:")
    if servicio is None:
        return None
    servicio_id, nombre, _ = servicio

    confirmar = inquirer.confirm(
        message=f"¿Eliminar '{nombre}' y todo su historial de pagos? No se puede deshacer.",
        default=False,
        **CANCELABLE,
    ).execute()
    if not confirmar:
        return _aviso("Eliminación cancelada.")

    if db.eliminar_servicio(servicio_id):
        return _exito(f"Servicio '{nombre}' e historial eliminados.")
    return _aviso("El servicio ya no estaba disponible.")


def modificar_servicio_prompt() -> Optional[str]:
    """Permite modificar un servicio recurrente desde este mes o el próximo."""
    servicios = db.obtener_servicios()
    if not servicios:
        return _aviso("No hay servicios para modificar.")

    servicio = _elegir_servicio("Selecciona el servicio que deseas modificar:")
    if servicio is None:
        return None
    servicio_id, nombre_actual, monto_actual = servicio

    existentes = {nombre.casefold() for s_id, nombre, _ in servicios if s_id != servicio_id}
    nombre = inquirer.text(
        message="Nombre del servicio:",
        default=nombre_actual,
        validate=lambda val: _validar_nombre(val, existentes),
        long_instruction=AYUDA_CANCELAR,
        **CANCELABLE,
    ).execute()
    if nombre is None:
        return _aviso("Modificación cancelada.")
    nombre = nombre.strip()

    monto = _pedir_monto("Monto mensual ($):", default=monto_editable(monto_actual))
    if monto is None:
        return _aviso("Modificación cancelada.")

    if nombre == nombre_actual and monto == monto_actual:
        return _aviso("No hubo cambios.")

    actual = _periodo_actual()
    siguiente = db.periodo_siguiente(actual)
    desde_periodo = inquirer.select(
        message="¿Desde cuándo aplica el cambio?",
        choices=[
            Choice(value=siguiente, name=f"Desde el próximo mes ({nombre_periodo(siguiente)})"),
            Choice(value=actual, name=f"Desde este mes ({nombre_periodo(actual)})"),
        ],
        pointer=PUNTERO,
        long_instruction="Los meses anteriores conservan su nombre y monto  •  " + AYUDA_CANCELAR,
        **CANCELABLE,
    ).execute()
    if desde_periodo is None:
        return _aviso("Modificación cancelada.")

    try:
        actualizado = db.actualizar_servicio(servicio_id, nombre, monto, desde_periodo)
    except sqlite3.IntegrityError:
        return _error(f"Ya existe un servicio llamado '{nombre}'.")

    if actualizado:
        return _exito(f"'{nombre}' actualizado desde {nombre_periodo(desde_periodo)}.")
    return _aviso("El servicio ya no está disponible.")


def mostrar_servicios() -> None:
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
        _pausa()
        return

    tabla = Table(
        title="Servicios recurrentes",
        header_style="bold cyan",
        border_style="blue",
    )
    tabla.add_column("Servicio", style="bold")
    tabla.add_column("Monto mensual", justify="right", style="green")

    for _, nombre, monto in servicios:
        tabla.add_row(nombre, formatear_monto(monto))

    total_estimado = sum(monto for _, _, monto in servicios)
    tabla.add_section()
    tabla.add_row(
        Text(f"{len(servicios)} servicios", style="dim"),
        Text(formatear_monto(total_estimado), style="bold cyan"),
    )
    console.print(tabla)
    _pausa()


def _tabla_reporte(periodo: str):
    """Construye el reporte de un mes, o None si no hay servicios."""
    # Consultar un mes pasado no debe crear registros que no existían.
    pagos = db.obtener_pagos_mes(periodo, generar=periodo >= _periodo_actual())
    if not pagos:
        return None

    tabla = Table(header_style="bold cyan", border_style="blue")
    tabla.add_column("Estado", justify="center", width=11)
    tabla.add_column("Servicio", style="bold")
    tabla.add_column("Monto", justify="right")
    # Primero los pendientes: son los que requieren atención.
    for _, servicio, monto, pagado in sorted(pagos, key=lambda pago: pago[3]):
        estilo = "green" if pagado else "yellow"
        estado = f"{ICONO_OK} PAGADO" if pagado else "PENDIENTE"
        tabla.add_row(Text(estado, style=estilo), servicio, Text(formatear_monto(monto), style=estilo))

    return Group(tabla, Text(), _resumen_mes(pagos))


def mostrar_reporte_mes(periodo: str) -> None:
    """Muestra el detalle de pagos realizados y pendientes de un mes."""
    contenido = _tabla_reporte(periodo)
    console.print(
        Panel(
            contenido or Text("No hay pagos registrados para este período. Usa «Marcar pagos» para cargarlos.", style="yellow"),
            title=f"[bold cyan]REPORTE FINANCIERO · {nombre_periodo(periodo).upper()}[/bold cyan]",
            border_style="cyan" if contenido else "yellow",
            padding=(1, 2),
        )
    )


def explorar_meses(periodo: str) -> None:
    """Muestra el reporte de un mes y permite moverse entre meses y marcar pagos."""
    aviso = None
    while True:
        console.clear()
        mostrar_reporte_mes(periodo)
        if aviso:
            console.print(aviso)
            aviso = None

        anterior = db.periodo_anterior(periodo)
        siguiente = db.periodo_siguiente(periodo)
        accion = inquirer.select(
            message=f"{nombre_periodo(periodo)} · ¿qué quieres hacer?",
            choices=[
                Choice(value="marcar", name="√  Marcar o desmarcar pagos de este mes"),
                Choice(value="anterior", name=f"◄  Mes anterior ({nombre_periodo(anterior)})"),
                Choice(value="siguiente", name=f"►  Mes siguiente ({nombre_periodo(siguiente)})"),
                Choice(value="ir", name="»  Ir a otro mes..."),
                Separator("──────────────────────"),
                Choice(value=None, name="←  Volver al menú"),
            ],
            pointer=PUNTERO,
            long_instruction=AYUDA_CANCELAR,
            **CANCELABLE,
        ).execute()

        if accion == "marcar":
            console.clear()
            aviso = gestionar_mes(periodo)
        elif accion == "anterior":
            periodo = anterior
        elif accion == "siguiente":
            periodo = siguiente
        elif accion == "ir":
            elegido = _pedir_periodo(periodo)
            if elegido:
                periodo = elegido
        else:
            return


def _pedir_periodo(default: str) -> Optional[str]:
    valor = inquirer.text(
        message="Período (YYYY-MM):",
        default=default,
        validate=lambda val: db.es_periodo_valido(val.strip()) or "Ingresa un mes válido, por ejemplo 2026-03.",
        long_instruction=AYUDA_CANCELAR,
        **CANCELABLE,
    ).execute()
    return valor.strip() if valor else None


def mostrar_historial() -> None:
    """Muestra el avance de los últimos meses registrados."""
    historial = db.obtener_historial()
    if not historial:
        console.print(_aviso("Todavía no hay meses registrados."))
        _pausa()
        return

    tabla = Table(title="Historial de los últimos meses", header_style="bold cyan", border_style="blue")
    tabla.add_column("Mes", style="bold")
    tabla.add_column("Avance")
    tabla.add_column("Pagado", justify="right", style="green")
    tabla.add_column("Pendiente", justify="right", style="yellow")
    tabla.add_column("Total", justify="right", style="bold cyan")
    for periodo, cantidad, pagados, total, total_pagado in historial:
        tabla.add_row(
            nombre_periodo(periodo),
            _barra_progreso(pagados, cantidad, ancho=10),
            formatear_monto(total_pagado),
            formatear_monto(total - total_pagado),
            formatear_monto(total),
        )
    console.print(tabla)
    _pausa()


def menu_principal():
    """Bucle del menú interactivo principal."""
    db.init_db()
    try:
        _bucle_menu()
    except KeyboardInterrupt:
        pass
    console.print("[bold cyan]¡Hasta luego![/bold cyan]")


def _bucle_menu():
    aviso = None
    while True:
        periodo_actual = _periodo_actual()
        console.clear()
        _mostrar_encabezado(periodo_actual, aviso)
        aviso = None

        opcion = inquirer.select(
            message="Elige una opción:",
            choices=[
                Separator("── Pagos ─────────────"),
                Choice(value="mes_actual", name=f"√  Marcar pagos de {nombre_periodo(periodo_actual)}"),
                Choice(value="explorar", name="≡  Ver detalle y navegar entre meses"),
                Choice(value="historial", name="∑  Historial de los últimos meses"),
                Separator("── Servicios ─────────"),
                Choice(value="ver_servicios", name="•  Ver servicios recurrentes"),
                Choice(value="nuevo_servicio", name="+  Agregar un servicio"),
                Choice(value="modificar_servicio", name="±  Modificar un servicio"),
                Choice(value="eliminar_servicio", name="×  Eliminar un servicio"),
                Separator("──────────────────────"),
                Choice(value="salir", name="←  Salir"),
            ],
            pointer=PUNTERO,
            long_instruction="↑/↓ moverse  •  Enter elegir  •  Ctrl+C salir",
        ).execute()

        if opcion == "mes_actual":
            console.clear()
            aviso = gestionar_mes(periodo_actual)
        elif opcion == "explorar":
            explorar_meses(periodo_actual)
        elif opcion == "historial":
            console.clear()
            mostrar_historial()
        elif opcion == "ver_servicios":
            console.clear()
            mostrar_servicios()
        elif opcion == "nuevo_servicio":
            aviso = agregar_servicio_prompt()
        elif opcion == "modificar_servicio":
            aviso = modificar_servicio_prompt()
        elif opcion == "eliminar_servicio":
            aviso = eliminar_servicio_prompt()
        elif opcion == "salir":
            return
