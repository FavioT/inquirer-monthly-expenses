import unittest
from io import StringIO
from unittest.mock import Mock, patch

from rich.console import Console

import cli_interactiva
from cli_interactiva import _barra_progreso
from formato import formatear_monto


class ProgressBarTests(unittest.TestCase):
    def test_currency_uses_spanish_grouping_and_decimal_separators(self):
        self.assertEqual(formatear_monto(150000), "$150.000,00")
        self.assertEqual(formatear_monto(1234.5), "$1.234,50")
        self.assertEqual(formatear_monto(0.75), "$0,75")

    def test_progress_bar_shows_completed_count_and_percentage(self):
        barra = _barra_progreso(2, 4)

        self.assertIn("50% (2/4)", barra.plain)
        self.assertEqual(len(barra.plain.split("  ")[0]), 20)

    def test_progress_bar_handles_empty_lists(self):
        barra = _barra_progreso(0, 0)

        self.assertIn("0% (0/0)", barra.plain)

    def test_report_displays_paid_and_pending_items_together(self):
        output = StringIO()
        console = Console(file=output, width=100, color_system=None)
        prompt = Mock()
        prompt.execute.return_value = ""

        with (
            patch.object(cli_interactiva, "console", console),
            patch.object(cli_interactiva.db, "obtener_resumen_mes", return_value=(
                [("Internet", 1200.0)],
                [("Electricidad", 800.0)],
            )),
            patch.object(cli_interactiva.inquirer, "text", return_value=prompt),
        ):
            cli_interactiva.mostrar_reporte_mes("2026-10")

        rendered = output.getvalue()
        self.assertIn("REPORTE FINANCIERO", rendered)
        self.assertIn("Internet", rendered)
        self.assertIn("Electricidad", rendered)
        self.assertIn("Total del mes", rendered)


if __name__ == "__main__":
    unittest.main()
