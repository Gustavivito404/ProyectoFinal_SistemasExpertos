import os
import sqlite3
import json

# ============================================================
# probar_bd.py
# Prueba rápida para verificar que los datos principales fueron
# cargados correctamente en SQLite.
#
# Recomendación de ejecución desde la raíz del proyecto:
#   python src/probar_bd.py
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(BASE_DIR, "bd", "sistema_incendio.db")


def mostrar_titulo(texto):
    print("\n" + "=" * 70)
    print(texto)
    print("=" * 70)


def texto_json_a_lista(texto):
    if not texto:
        return []

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        return []


conexion = sqlite3.connect(RUTA_BD)
conexion.row_factory = sqlite3.Row
cursor = conexion.cursor()

# ============================================================
# CLIENTES
# ============================================================

mostrar_titulo("CLIENTES REGISTRADOS")
cursor.execute("""
SELECT
    id_cliente,
    nombre,
    tipo,
    num_operaciones,
    cliente_frecuente,
    fecha_ultimo_servicio,
    bomba_electrica,
    bomba_piloto,
    bomba_combustion,
    tablero_control_propio,
    rfc,
    direccion
FROM clientes
ORDER BY id_cliente
""")

for cliente in cursor.fetchall():
    print(
        f"{cliente['id_cliente']} | {cliente['nombre']} | {cliente['tipo']} | "
        f"Operaciones: {cliente['num_operaciones']} | "
        f"Frecuente: {'Sí' if cliente['cliente_frecuente'] else 'No'} | "
        f"Último servicio: {cliente['fecha_ultimo_servicio']}"
    )
    print(
        f"  Equipo -> Eléctrica: {cliente['bomba_electrica']}, "
        f"Piloto: {cliente['bomba_piloto']}, "
        f"Combustión: {cliente['bomba_combustion']}, "
        f"Tablero propio: {cliente['tablero_control_propio']}"
    )
    print(f"  Facturación -> RFC: {cliente['rfc']} | Dirección: {cliente['direccion']}")

# ============================================================
# PRODUCTOS
# ============================================================

mostrar_titulo("PRODUCTOS REGISTRADOS")
cursor.execute("""
SELECT
    id_producto,
    nombre,
    categoria,
    subcategoria,
    potencia_hp,
    precio,
    stock,
    stock_minimo,
    instalable,
    equipo_critico,
    precio_variable,
    control_stock,
    requiere_diseno_tecnico
FROM productos
ORDER BY id_producto
""")

for producto in cursor.fetchall():
    print(
        f"{producto['id_producto']} | {producto['nombre']} | "
        f"{producto['categoria']} / {producto['subcategoria']} | "
        f"{producto['potencia_hp']} HP | ${producto['precio']} | "
        f"Stock: {producto['stock']} | Mínimo: {producto['stock_minimo']}"
    )
    print(
        f"  Instalable: {producto['instalable']} | "
        f"Crítico: {producto['equipo_critico']} | "
        f"Precio variable: {producto['precio_variable']} | "
        f"Control stock: {producto['control_stock']} | "
        f"Diseño técnico: {producto['requiere_diseno_tecnico']}"
    )

# ============================================================
# SERVICIOS
# ============================================================

mostrar_titulo("SERVICIOS REGISTRADOS")
cursor.execute("""
SELECT
    id_servicio,
    nombre,
    tipo_servicio,
    costo_base,
    duracion_dias_base,
    nivel_validacion,
    considera_ultimo_servicio,
    requiere_revision_previa,
    observaciones_base
FROM servicios
ORDER BY id_servicio
""")

for servicio in cursor.fetchall():
    observaciones = texto_json_a_lista(servicio["observaciones_base"])
    print(
        f"{servicio['id_servicio']} | {servicio['nombre']} | "
        f"Tipo: {servicio['tipo_servicio']} | "
        f"Costo base: ${servicio['costo_base']} | "
        f"Duración base: {servicio['duracion_dias_base']} día(s) | "
        f"Validación: {servicio['nivel_validacion']}"
    )
    print(
        f"  Considera último servicio: {servicio['considera_ultimo_servicio']} | "
        f"Revisión previa: {servicio['requiere_revision_previa']} | "
        f"Observaciones: {len(observaciones)}"
    )

# ============================================================
# REGLAS DE INFERENCIA
# ============================================================

mostrar_titulo("REGLAS DE INFERENCIA REGISTRADAS")
cursor.execute("""
SELECT
    categoria,
    COUNT(*) AS total
FROM reglas_inferencia
GROUP BY categoria
ORDER BY categoria
""")

for grupo in cursor.fetchall():
    print(f"{grupo['categoria']}: {grupo['total']} regla(s)")

cursor.execute("SELECT COUNT(*) AS total FROM reglas_inferencia")
total_reglas = cursor.fetchone()["total"]
print(f"Total de reglas cargadas: {total_reglas}")

# ============================================================
# ALIAS DE PRODUCTOS
# ============================================================

mostrar_titulo("ALIAS DE PRODUCTOS")
cursor.execute("SELECT COUNT(*) AS total FROM alias_productos")
total_alias = cursor.fetchone()["total"]
print(f"Total de alias cargados: {total_alias}")

cursor.execute("""
SELECT id_producto, nombre_producto, alias
FROM alias_productos
ORDER BY id_producto, alias
LIMIT 10
""")

print("Primeros 10 alias:")
for alias in cursor.fetchall():
    print(f"{alias['id_producto']} | {alias['nombre_producto']} -> {alias['alias']}")

# ============================================================
# USUARIOS INTERNOS
# ============================================================

mostrar_titulo("USUARIOS INTERNOS")
cursor.execute("""
SELECT
    id_usuario,
    nombre,
    rol,
    nivel_validacion,
    puede_autorizar_servicios,
    requiere_supervision_tecnica
FROM usuarios_internos
ORDER BY id_usuario
""")

for usuario in cursor.fetchall():
    servicios = texto_json_a_lista(usuario["puede_autorizar_servicios"])
    print(
        f"{usuario['id_usuario']} | {usuario['nombre']} | "
        f"Rol: {usuario['rol']} | "
        f"Nivel: {usuario['nivel_validacion']} | "
        f"Autoriza: {', '.join(servicios)} | "
        f"Requiere supervisión técnica: {'Sí' if usuario['requiere_supervision_tecnica'] else 'No'}"
    )

# ============================================================
# TABLAS OPERATIVAS
# ============================================================

mostrar_titulo("TABLAS OPERATIVAS CREADAS")
tablas_operativas = [
    "pedidos",
    "detalle_pedidos",
    "solicitudes_servicio",
    "inferencias"
]

for tabla in tablas_operativas:
    cursor.execute(f"SELECT COUNT(*) AS total FROM {tabla}")
    total = cursor.fetchone()["total"]
    print(f"{tabla}: {total} registro(s)")

conexion.close()
print("\nPrueba de base de datos finalizada correctamente.")
