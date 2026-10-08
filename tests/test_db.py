import tempfile
import sqlite3
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

    def test_service_update_preserves_previous_periods_and_updates_future_ones(self):
        db.agregar_servicio("Internet", 25000.0)
        servicio_id = db.obtener_servicios()[0][0]
        pago_octubre = db.obtener_pagos_mes("2026-10")[0][0]
        db.obtener_pagos_mes("2026-11")
        pago_diciembre = db.obtener_pagos_mes("2026-12")[0][0]
        db.toggle_pago(pago_diciembre)

        self.assertTrue(db.actualizar_servicio(servicio_id, "Fibra", 30000.0, "2026-11"))

        self.assertEqual(db.obtener_pagos_mes("2026-10"), [(pago_octubre, "Internet", 25000.0, 0)])
        self.assertEqual(db.obtener_pagos_mes("2026-11")[0][1:], ("Fibra", 30000.0, 0))
        self.assertEqual(db.obtener_pagos_mes("2026-12")[0][1:], ("Fibra", 30000.0, 1))
        self.assertEqual(db.obtener_pagos_mes("2027-01")[0][1:], ("Fibra", 30000.0, 0))
        self.assertEqual(db.obtener_servicios(), [(servicio_id, "Fibra", 30000.0)])

    def test_service_update_validates_data_and_reports_missing_service(self):
        with self.assertRaises(ValueError):
            db.actualizar_servicio(1, "Internet", -1.0, "2026-11")
        with self.assertRaises(ValueError):
            db.actualizar_servicio(1, "Internet", 100.0, "2026-13")
        self.assertFalse(db.actualizar_servicio(1, "Internet", 100.0, "2026-11"))

    def test_next_period_handles_year_boundary(self):
        self.assertEqual(db.periodo_siguiente("2026-12"), "2027-01")

    def test_existing_database_gets_a_baseline_service_version(self):
        legacy_path = Path(self.temp_dir.name) / "legacy.db"
        with sqlite3.connect(legacy_path) as conn:
            conn.execute("""
                CREATE TABLE servicios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    monto_estimado REAL DEFAULT 0.0
                )
            """)
            conn.execute("""
                CREATE TABLE pagos_mes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    servicio_id INTEGER NOT NULL,
                    mes_año TEXT NOT NULL,
                    monto REAL NOT NULL,
                    pagado INTEGER DEFAULT 0,
                    UNIQUE(servicio_id, mes_año)
                )
            """)
            conn.execute(
                "INSERT INTO servicios (id, nombre, monto_estimado) VALUES (1, 'Internet', 25000)",
            )
            conn.execute(
                "INSERT INTO pagos_mes (id, servicio_id, mes_año, monto, pagado) VALUES (7, 1, '2026-10', 20000, 1)",
            )
            conn.commit()
        conn.close()

        with patch.object(db, "DB_NAME", legacy_path):
            db.init_db()
            self.assertEqual(
                db.obtener_pagos_mes("2026-10"),
                [(7, "Internet", 20000.0, 1)]
            )


if __name__ == "__main__":
    unittest.main()
