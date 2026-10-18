import unittest
from io import StringIO
from unittest.mock import Mock, patch

from rich.console import Console

import cli_interactiva
from cli_interactiva import _barra_progreso
from formato import formatear_monto, monto_editable, nombre_periodo, parsear_monto


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

        with (
            patch.object(cli_interactiva, "console", console),
            patch.object(cli_interactiva.db, "obtener_pagos_mes", return_value=[
                (1, "Internet", 1200.0, 1),
                (2, "Electricidad", 800.0, 0),
            ]),
        ):
            cli_interactiva.mostrar_reporte_mes("2026-10")

        rendered = output.getvalue()
        self.assertIn("REPORTE FINANCIERO", rendered)
        self.assertIn("Internet", rendered)
        self.assertIn("Electricidad", rendered)
        self.assertIn("Total del mes", rendered)
        self.assertIn("OCTUBRE 2026", rendered)
        self.assertLess(rendered.index("Electricidad"), rendered.index("Internet"))

    def test_checklist_cancel_keeps_payments_unchanged(self):
        prompt = Mock()
        prompt.execute.return_value = None
        console = Console(file=StringIO(), width=100, color_system=None)

        with (
            patch.object(cli_interactiva, "console", console),
            patch.object(cli_interactiva.db, "obtener_pagos_mes", return_value=[(1, "Luz", 10.0, 0)]),
            patch.object(cli_interactiva.db, "guardar_estado_pagos") as guardar,
            patch.object(cli_interactiva.inquirer, "checkbox", return_value=prompt),
        ):
            mensaje = cli_interactiva.gestionar_mes("2026-10")

        guardar.assert_not_called()
        self.assertIn("descartados", mensaje)

    def test_checklist_reports_which_services_changed(self):
        prompt = Mock()
        prompt.execute.return_value = [2]
        console = Console(file=StringIO(), width=100, color_system=None)

        with (
            patch.object(cli_interactiva, "console", console),
            patch.object(cli_interactiva.db, "obtener_pagos_mes", return_value=[
                (1, "Luz", 10.0, 1),
                (2, "Gas", 20.0, 0),
            ]),
            patch.object(cli_interactiva.db, "guardar_estado_pagos") as guardar,
            patch.object(cli_interactiva.inquirer, "checkbox", return_value=prompt),
        ):
            mensaje = cli_interactiva.gestionar_mes("2026-10")

        guardar.assert_called_once_with("2026-10", {2})
        self.assertIn("pagado: Gas", mensaje)
        self.assertIn("pendiente: Luz", mensaje)


class FormatoTests(unittest.TestCase):
    def test_amounts_accept_local_and_plain_formats(self):
        casos = {
            "25000": 25000.0,
            "25.000": 25000.0,
            "1.234.567": 1234567.0,
            "25.000,50": 25000.5,
            "$ 1.234,5": 1234.5,
            "1234.5": 1234.5,
            "0,75": 0.75,
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(parsear_monto(texto), esperado)

    def test_amounts_reject_invalid_values(self):
        for texto in ("", "abc", "-5", "inf", "nan"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    parsear_monto(texto)

    def test_editable_amount_round_trips(self):
        self.assertEqual(monto_editable(25000.5), "25.000,50")
        self.assertEqual(parsear_monto(monto_editable(25000.5)), 25000.5)

    def test_period_name_is_in_spanish(self):
        self.assertEqual(nombre_periodo("2026-01"), "Enero 2026")


if __name__ == "__main__":
    unittest.main()
