# 💸 Gestor de Pagos Mensuales (CLI)

Una herramienta interactiva de línea de comandos (CLI/TUI) desarrollada en Python para llevar el control de tus gastos y servicios recurrentes mes a mes mediante una lista de verificación (*checkbox*).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg)
![InquirerPy](https://img.shields.io/badge/Interface-InquirerPy-orange.svg)

---

## 🚀 Características

- **Plantilla de servicios fijos:** Registra tus servicios recurrentes una sola vez (ej: *Luz*, *Internet*, *Alquiler*).
- **Checklist por mes:** Interfaz navegable con teclado para tildar `[x]` o destildar `[ ]` cada pago en el mes correspondiente sin afectar períodos anteriores o futuros.
- **Reportes financieros:** Visualización clara de gastos pagados vs. pendientes, junto con los totales del mes en curso.
- **Base de datos local:** Todo se almacena localmente en SQLite (`pagos.db`).
- **Navegación por menús:** Interfaz interactiva para la terminal usando **InquirerPy** y formato con **Rich**.

---

## 🛠️ Requisitos Previos

- **Python** 3.8 o superior.
- Git (opcional).

---

## 📦 Instalación y Configuración

1. **Clona el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/gestor-pagos.git](https://github.com/tu-usuario/gestor-pagos.git)
   cd gestor-pagos
