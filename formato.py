import math
import re

MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

# Símbolos incluidos en las fuentes habituales de la consola de Windows
# (Consolas, Lucida Console, Cascadia), para que no se vean como cuadrados.
ICONO_OK = "√"
ICONO_ERROR = "×"
ICONO_AVISO = "!"
PUNTERO = "►"


def formatear_monto(monto: float) -> str:
    """Formatea un importe con punto para miles y coma para decimales."""
    return f"${monto:,.2f}".translate(str.maketrans({",": ".", ".": ","}))


def monto_editable(monto: float) -> str:
    """Devuelve el monto sin signo, listo para usar como valor por defecto en un formulario."""
    return formatear_monto(monto).lstrip("$")


def parsear_monto(texto: str) -> float:
    """Interpreta montos como '25000', '25.000', '25.000,50', '$ 1.234,5' o '1234.5'."""
    limpio = texto.strip().replace("$", "").replace(" ", "")
    if not limpio:
        raise ValueError("El monto no puede estar vacío.")

    if "," in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", limpio):
        limpio = limpio.replace(".", "")

    monto = float(limpio)
    if not math.isfinite(monto) or monto < 0:
        raise ValueError("El monto debe ser un número finito mayor o igual a cero.")
    return monto


def es_monto_valido(texto: str) -> bool:
    try:
        parsear_monto(texto)
    except ValueError:
        return False
    return True


def nombre_periodo(periodo: str) -> str:
    """Convierte '2026-10' en 'Octubre 2026'."""
    año, mes = periodo.split("-")
    return f"{MESES[int(mes) - 1].capitalize()} {año}"
