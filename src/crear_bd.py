import os
import sqlite3

# ============================================================
# crear_bd.py
# Crea una base de datos SQLite limpia para el sistema experto
# contra incendio.
#
# Recomendación de ejecución desde la raíz del proyecto:
#   python src/crear_bd.py
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(BASE_DIR, "bd", "sistema_incendio.db")

os.makedirs(os.path.dirname(RUTA_BD), exist_ok=True)

conexion = sqlite3.connect(RUTA_BD)
cursor = conexion.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

# ============================================================
# RECREAR TABLAS
# Nota: Este script reconstruye la base de datos desde cero.
# Si ya tienes datos reales capturados, respalda el archivo .db
# antes de ejecutarlo.
# ============================================================

tablas = [
    "inferencias",
    "detalle_pedidos",
    "pedidos",
    "solicitudes_servicio",
    "alias_productos",
    "usuarios_internos",
    "reglas_inferencia",
    "servicios",
    "productos",
    "clientes"
]

for tabla in tablas:
    cursor.execute(f"DROP TABLE IF EXISTS {tabla}")

# ============================================================
# TABLA: CLIENTES
# ============================================================

cursor.execute("""
CREATE TABLE clientes (
    id_cliente TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    num_operaciones INTEGER NOT NULL DEFAULT 0,
    cliente_frecuente INTEGER NOT NULL DEFAULT 0,
    fecha_ultimo_servicio TEXT,

    bomba_electrica INTEGER NOT NULL DEFAULT 0,
    bomba_piloto INTEGER NOT NULL DEFAULT 0,
    bomba_combustion INTEGER NOT NULL DEFAULT 0,
    tablero_control_propio INTEGER NOT NULL DEFAULT 0,

    rfc TEXT,
    direccion TEXT
)
""")

# ============================================================
# TABLA: PRODUCTOS
# ============================================================

cursor.execute("""
CREATE TABLE productos (
    id_producto TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    subcategoria TEXT,
    potencia_hp REAL NOT NULL DEFAULT 0,
    precio REAL NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 0,

    instalable INTEGER NOT NULL DEFAULT 0,
    equipo_critico INTEGER NOT NULL DEFAULT 0,
    requiere_mantenimiento INTEGER NOT NULL DEFAULT 0,
    precio_variable INTEGER NOT NULL DEFAULT 0,
    control_stock INTEGER NOT NULL DEFAULT 1,
    requiere_diseno_tecnico INTEGER NOT NULL DEFAULT 0
)
""")

# ============================================================
# TABLA: SERVICIOS
# observaciones_base se guarda como texto JSON.
# ============================================================

cursor.execute("""
CREATE TABLE servicios (
    id_servicio TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo_servicio TEXT NOT NULL,
    costo_base REAL NOT NULL DEFAULT 0,
    duracion_dias_base INTEGER NOT NULL DEFAULT 1,
    nivel_validacion TEXT NOT NULL,
    considera_ultimo_servicio INTEGER NOT NULL DEFAULT 0,
    requiere_revision_previa INTEGER NOT NULL DEFAULT 0,
    observaciones_base TEXT
)
""")

# ============================================================
# TABLA: REGLAS DE INFERENCIA
# condiciones y acciones se guardan como texto JSON.
# ============================================================

cursor.execute("""
CREATE TABLE reglas_inferencia (
    id_regla TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    prioridad TEXT NOT NULL,
    agente_responsable TEXT NOT NULL,
    condiciones TEXT NOT NULL,
    acciones TEXT NOT NULL,
    explicacion TEXT
)
""")

# ============================================================
# TABLA: ALIAS DE PRODUCTOS
# Un alias por fila para facilitar búsquedas del Agente 1.
# ============================================================

cursor.execute("""
CREATE TABLE alias_productos (
    id_alias INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto TEXT NOT NULL,
    nombre_producto TEXT NOT NULL,
    alias TEXT NOT NULL,
    FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
)
""")

# ============================================================
# TABLA: USUARIOS INTERNOS
# Las listas puede_validar y puede_autorizar_servicios se guardan
# como texto JSON para mantener simple la primera versión.
# ============================================================

cursor.execute("""
CREATE TABLE usuarios_internos (
    id_usuario TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL,
    nivel_validacion TEXT NOT NULL,
    puede_validar TEXT NOT NULL,
    puede_autorizar_servicios TEXT NOT NULL,
    requiere_supervision_tecnica INTEGER NOT NULL DEFAULT 0
)
""")

# ============================================================
# TABLA: PEDIDOS
# Para ventas/cotizaciones de productos.
# ============================================================

cursor.execute("""
CREATE TABLE pedidos (
    id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente TEXT,
    fecha TEXT NOT NULL,
    tipo_pedido TEXT NOT NULL,
    total REAL NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    resumen TEXT,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
)
""")

# ============================================================
# TABLA: DETALLE_PEDIDOS
# Productos asociados a un pedido.
# ============================================================

cursor.execute("""
CREATE TABLE detalle_pedidos (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido INTEGER NOT NULL,
    id_producto TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido),
    FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
)
""")

# ============================================================
# TABLA: SOLICITUDES DE SERVICIO
# Para mantenimiento, correctivo, inspección e instalación.
# ============================================================

cursor.execute("""
CREATE TABLE solicitudes_servicio (
    id_solicitud INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente TEXT,
    id_servicio TEXT NOT NULL,
    fecha TEXT NOT NULL,
    descripcion_cliente TEXT,
    ubicacion_servicio TEXT,
    servicio_foraneo INTEGER NOT NULL DEFAULT 0,

    costo_base REAL NOT NULL DEFAULT 0,
    duracion_dias_base INTEGER NOT NULL DEFAULT 1,
    nivel_validacion TEXT,
    requiere_revision_previa INTEGER NOT NULL DEFAULT 0,

    estado TEXT NOT NULL DEFAULT 'pendiente_validacion',
    resumen_supervisor TEXT,

    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
)
""")

# ============================================================
# TABLA: INFERENCIAS
# Historial explicable de reglas activadas por operación.
# tipo_operacion puede ser: pedido, servicio, cliente, producto, etc.
# ============================================================

cursor.execute("""
CREATE TABLE inferencias (
    id_inferencia INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_operacion TEXT NOT NULL,
    id_operacion INTEGER,
    id_regla TEXT,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    mensaje_original TEXT,
    intencion_detectada TEXT,
    condicion_evaluada TEXT,
    accion_realizada TEXT,
    resultado TEXT NOT NULL,
    explicacion TEXT,

    FOREIGN KEY (id_regla) REFERENCES reglas_inferencia(id_regla)
)
""")

conexion.commit()
conexion.close()

print("Base de datos creada correctamente en:", RUTA_BD)
