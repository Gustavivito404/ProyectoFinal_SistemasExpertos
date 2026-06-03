import sqlite3
import os

# Ruta de la base de datos
RUTA_BD = os.path.join("bd", "sistema_incendio.db")

# Crear carpeta bd si no existe
os.makedirs("bd", exist_ok=True)

# Conexión a SQLite
conexion = sqlite3.connect(RUTA_BD)
cursor = conexion.cursor()

# =========================
# TABLA: CLIENTES
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    cliente_frecuente INTEGER NOT NULL,
    ultima_compra_dias INTEGER
)
""")

# =========================
# TABLA: PRODUCTOS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
    id_producto TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    potencia_hp REAL,
    precio REAL NOT NULL,
    stock INTEGER NOT NULL
)
""")

# =========================
# TABLA: SERVICIOS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS servicios (
    id_servicio TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    costo REAL NOT NULL,
    duracion_horas REAL,
    descripcion TEXT
)
""")

# =========================
# TABLA: PEDIDOS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente TEXT,
    fecha TEXT NOT NULL,
    tipo_pedido TEXT NOT NULL,
    total REAL,
    estado TEXT,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
)
""")

# =========================
# TABLA: DETALLE_PEDIDOS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS detalle_pedidos (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido INTEGER,
    id_producto TEXT,
    cantidad INTEGER,
    subtotal REAL,
    FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido),
    FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
)
""")

# =========================
# TABLA: INFERENCIAS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS inferencias (
    id_inferencia INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido INTEGER,
    regla_aplicada TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    resultado TEXT NOT NULL,
    FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido)
)
""")

conexion.commit()
conexion.close()

print("Base de datos creada correctamente en:", RUTA_BD)