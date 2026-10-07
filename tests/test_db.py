import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import db


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "pagos.db"
        self.db_name_patch = patch.object(db, "DB_NAME", self.database_path)
        self.db_name_patch.start()
        db.init_db()

    def tearDown(self):
        self.db_name_patch.stop()
        self.temp_dir.cleanup()

    def test_period_validation_rejects_invalid_months(self):
        self.assertTrue(db.es_periodo_valido("2026-10"))
        self.assertFalse(db.es_periodo_valido("2026-13"))
        self.assertFalse(db.es_periodo_valido("2026-1"))
        self.assertFalse(db.es_periodo_valido("2026-00"))

    def test_invalid_period_is_rejected_before_creating_month_records(self):
        with self.assertRaises(ValueError):
            db.generar_pagos_del_mes("2026-13")

    def test_payment_can_be_toggled_and_missing_payment_is_reported(self):
        db.agregar_servicio("Internet", 25000.0)
        pagos = db.obtener_pagos_mes("2026-10")
        pago_id, _, _, estado_inicial = pagos[0]

        self.assertEqual(estado_inicial, 0)
        self.assertTrue(db.toggle_pago(pago_id))
        self.assertEqual(db.obtener_pagos_mes("2026-10")[0][3], 1)
        self.assertFalse(db.toggle_pago(-1))

    def test_service_deletion_reports_whether_it_existed(self):
        db.agregar_servicio("Luz", 1000.0)
        servicio_id = db.obtener_servicios()[0][0]
        db.obtener_pagos_mes("2026-10")

        self.assertTrue(db.eliminar_servicio(servicio_id))
        self.assertFalse(db.eliminar_servicio(servicio_id))
        self.assertEqual(db.obtener_pagos_mes("2026-10"), [])

    def test_service_rejects_invalid_amounts_and_blank_names(self):
        for amount in (-1.0, float("inf"), float("nan")):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    db.agregar_servicio("Internet", amount)

        with self.assertRaises(ValueError):
            db.agregar_servicio("  ", 10.0)


if __name__ == "__main__":
    unittest.main()
