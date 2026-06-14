import os
import sqlite3

# ============================================================
# crear_bd.py
# Crea una base de datos SQLite limpia para el sistema experto
# contra incendio.
#
# Ejecutar desde la raíz del proyecto:
#   py src/crear_bd.py
#
# IMPORTANTE:
# Este script elimina y recrea las tablas. Si ya tienes datos reales,
# respalda primero el archivo bd/sistema_incendio.db.
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(BASE_DIR, "bd", "sistema_incendio.db")

os.makedirs(os.path.dirname(RUTA_BD), exist_ok=True)

conexion = sqlite3.connect(RUTA_BD)
cursor = conexion.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

# ============================================================
# RECREAR TABLAS
# ============================================================

tablas = [
    "mensajes_chat_cliente",
    "conversaciones_cliente",
    "inferencias",
    "validaciones_servicio",
    "movimientos_inventario",
    "detalle_pedidos",
    "pedidos",
    "solicitudes_servicio",
    "clientes_preliminares",
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
# Clientes ya validados y registrados formalmente.
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
# TABLA: CLIENTES PRELIMINARES
# Clientes capturados desde el chat público, pendientes de validar.
# ============================================================

cursor.execute("""
CREATE TABLE clientes_preliminares (
    id_preliminar INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    tipo TEXT,
    rfc TEXT,
    direccion TEXT,

    bomba_electrica INTEGER NOT NULL DEFAULT 0,
    bomba_piloto INTEGER NOT NULL DEFAULT 0,
    bomba_combustion INTEGER NOT NULL DEFAULT 0,
    tablero_control_propio INTEGER NOT NULL DEFAULT 0,

    estado TEXT NOT NULL DEFAULT 'pendiente_validacion',
    observaciones TEXT,
    fecha_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_validacion TEXT,
    id_usuario_validador TEXT,
    id_cliente_generado TEXT,

    FOREIGN KEY (id_usuario_validador) REFERENCES usuarios_internos(id_usuario),
    FOREIGN KEY (id_cliente_generado) REFERENCES clientes(id_cliente)
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
    contrasena TEXT NOT NULL,
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
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_pedido TEXT NOT NULL,
    total REAL NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'pendiente_validacion',
    resumen TEXT,
    id_usuario_validador TEXT,
    fecha_validacion TEXT,

    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_usuario_validador) REFERENCES usuarios_internos(id_usuario)
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
    id_cliente_preliminar INTEGER,
    id_servicio TEXT NOT NULL,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    mensaje_original TEXT,
    descripcion_cliente TEXT,
    ubicacion_servicio TEXT,
    servicio_foraneo INTEGER NOT NULL DEFAULT 0,

    costo_base REAL NOT NULL DEFAULT 0,
    costo_extra_distancia REAL NOT NULL DEFAULT 0,
    total_estimado REAL NOT NULL DEFAULT 0,
    duracion_dias_base INTEGER NOT NULL DEFAULT 1,
    nivel_validacion TEXT,
    requiere_revision_previa INTEGER NOT NULL DEFAULT 0,

    estado TEXT NOT NULL DEFAULT 'pendiente_validacion',
    resumen_supervisor TEXT,
    reglas_activadas TEXT,
    advertencias TEXT,
    recomendaciones TEXT,
    observaciones_logistica TEXT,

    id_usuario_creador TEXT,
    id_usuario_validador TEXT,
    fecha_validacion TEXT,

    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_cliente_preliminar) REFERENCES clientes_preliminares(id_preliminar),
    FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio),
    FOREIGN KEY (id_usuario_creador) REFERENCES usuarios_internos(id_usuario),
    FOREIGN KEY (id_usuario_validador) REFERENCES usuarios_internos(id_usuario)
)
""")

# ============================================================
# TABLA: MOVIMIENTOS DE INVENTARIO
# Historial de entradas, salidas, ventas, uso en servicio y ajustes.
# ============================================================

cursor.execute("""
CREATE TABLE movimientos_inventario (
    id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto TEXT NOT NULL,
    tipo_movimiento TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    stock_anterior INTEGER NOT NULL,
    stock_nuevo INTEGER NOT NULL,
    motivo TEXT,
    id_usuario TEXT,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_producto) REFERENCES productos(id_producto),
    FOREIGN KEY (id_usuario) REFERENCES usuarios_internos(id_usuario)
)
""")

# ============================================================
# TABLA: VALIDACIONES DE SERVICIO
# Registro de aprobaciones, rechazos o solicitudes de más información.
# ============================================================

cursor.execute("""
CREATE TABLE validaciones_servicio (
    id_validacion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_solicitud INTEGER NOT NULL,
    id_usuario TEXT,
    decision TEXT NOT NULL,
    comentarios TEXT,
    costo_extra_distancia REAL NOT NULL DEFAULT 0,
    total_estimado REAL,
    nueva_duracion_dias INTEGER,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_solicitud) REFERENCES solicitudes_servicio(id_solicitud),
    FOREIGN KEY (id_usuario) REFERENCES usuarios_internos(id_usuario)
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

# ============================================================
# TABLA: CONVERSACIONES DEL CHAT PÚBLICO
# Permite guardar un flujo conversacional básico sin login.
# ============================================================

cursor.execute("""
CREATE TABLE conversaciones_cliente (
    id_conversacion INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_inicio TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_interaccion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado TEXT NOT NULL DEFAULT 'abierta',
    intencion_detectada TEXT,
    id_cliente TEXT,
    id_cliente_preliminar INTEGER,
    id_solicitud INTEGER,

    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_cliente_preliminar) REFERENCES clientes_preliminares(id_preliminar),
    FOREIGN KEY (id_solicitud) REFERENCES solicitudes_servicio(id_solicitud)
)
""")

# ============================================================
# TABLA: MENSAJES DEL CHAT PÚBLICO
# Guarda mensajes cliente/agente para historial básico.
# ============================================================

cursor.execute("""
CREATE TABLE mensajes_chat_cliente (
    id_mensaje INTEGER PRIMARY KEY AUTOINCREMENT,
    id_conversacion INTEGER NOT NULL,
    remitente TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_conversacion) REFERENCES conversaciones_cliente(id_conversacion)
)
""")

conexion.commit()
conexion.close()

print("Base de datos creada correctamente en:", RUTA_BD)
