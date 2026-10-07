import sqlite3

DB_NAME = "pagos.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Tabla de servicios fijos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servicios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                monto_estimado REAL DEFAULT 0.0
            )
        """)
        
        # Tabla de pagos por mes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagos_mes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servicio_id INTEGER NOT NULL,
                mes_año TEXT NOT NULL,  -- YYYY-MM
                monto REAL NOT NULL,
                pagado INTEGER DEFAULT 0, -- 0 = Pendiente, 1 = Pagado
                FOREIGN KEY (servicio_id) REFERENCES servicios (id),
                UNIQUE(servicio_id, mes_año)
            )
        """)
        conn.commit()

def agregar_servicio(nombre: str, monto: float):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO servicios (nombre, monto_estimado) VALUES (?, ?)",
            (nombre, monto)
        )
        conn.commit()

def obtener_servicios():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, monto_estimado FROM servicios ORDER BY nombre")
        return cursor.fetchall()

def eliminar_servicio(servicio_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pagos_mes WHERE servicio_id = ?", (servicio_id,))
        cursor.execute("DELETE FROM servicios WHERE id = ?", (servicio_id,))
        conn.commit()

def generar_pagos_del_mes(mes_año: str):
    servicios = obtener_servicios()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        for s_id, nombre, monto in servicios:
            cursor.execute("""
                INSERT OR IGNORE INTO pagos_mes (servicio_id, mes_año, monto, pagado)
                VALUES (?, ?, ?, 0)
            """, (s_id, mes_año, monto))
        conn.commit()

def obtener_pagos_mes(mes_año: str):
    generar_pagos_del_mes(mes_año)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, s.nombre, p.monto, p.pagado
            FROM pagos_mes p
            JOIN servicios s ON p.servicio_id = s.id
            WHERE p.mes_año = ?
            ORDER BY s.nombre
        """, (mes_año,))
        return cursor.fetchall()

def guardar_estado_pagos(mes_año: str, ids_pagados: set):
    """Actualiza en lote los elementos marcados en la lista del mes."""
    pagos = obtener_pagos_mes(mes_año)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        for pago_id, _, _, _ in pagos:
            nuevo_estado = 1 if pago_id in ids_pagados else 0
            cursor.execute("UPDATE pagos_mes SET pagado = ? WHERE id = ?", (nuevo_estado, pago_id))
        conn.commit()

def obtener_resumen_mes(mes_año: str):
    """Devuelve listas separadas de pagos realizados y pendientes para un mes."""
    generar_pagos_del_mes(mes_año)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Obtener pagados
        cursor.execute("""
            SELECT s.nombre, p.monto 
            FROM pagos_mes p 
            JOIN servicios s ON p.servicio_id = s.id 
            WHERE p.mes_año = ? AND p.pagado = 1
            ORDER BY s.nombre
        """, (mes_año,))
        pagados = cursor.fetchall()

        # Obtener no pagados (pendientes)
        cursor.execute("""
            SELECT s.nombre, p.monto 
            FROM pagos_mes p 
            JOIN servicios s ON p.servicio_id = s.id 
            WHERE p.mes_año = ? AND p.pagado = 0
            ORDER BY s.nombre
        """, (mes_año,))
        pendientes = cursor.fetchall()

        return pagados, pendientes