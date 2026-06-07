import os
import json
import sqlite3

# ============================================================
# cargar_datos.py
# Carga los JSON base dentro de SQLite.
#
# Recomendación de ejecución desde la raíz del proyecto:
#   python src/cargar_datos.py
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(BASE_DIR, "bd", "sistema_incendio.db")
RUTA_DATOS = os.path.join(BASE_DIR, "datos")


def cargar_json(nombre_archivo):
    ruta = os.path.join(RUTA_DATOS, nombre_archivo)

    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")

    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def bool_a_int(valor):
    return 1 if bool(valor) else 0


def lista_a_json_texto(valor):
    return json.dumps(valor, ensure_ascii=False)


conexion = sqlite3.connect(RUTA_BD)
cursor = conexion.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

# ============================================================
# CARGAR CLIENTES
# ============================================================

clientes = cargar_json("clientes.json")

for cliente in clientes:
    equipo = cliente.get("equipo_instalado", {})
    facturacion = cliente.get("facturacion", {})

    cursor.execute("""
    INSERT OR REPLACE INTO clientes (
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
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente["id_cliente"],
        cliente["nombre"],
        cliente["tipo"],
        cliente.get("num_operaciones", 0),
        bool_a_int(cliente.get("cliente_frecuente", False)),
        cliente.get("fecha_ultimo_servicio"),
        bool_a_int(equipo.get("bomba_electrica", False)),
        bool_a_int(equipo.get("bomba_piloto", False)),
        bool_a_int(equipo.get("bomba_combustion", False)),
        bool_a_int(equipo.get("tablero_control_propio", False)),
        facturacion.get("rfc"),
        facturacion.get("direccion")
    ))

# ============================================================
# CARGAR PRODUCTOS
# ============================================================

productos = cargar_json("productos.json")

for producto in productos:
    cursor.execute("""
    INSERT OR REPLACE INTO productos (
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
        requiere_mantenimiento,
        precio_variable,
        control_stock,
        requiere_diseno_tecnico
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        producto["id_producto"],
        producto["nombre"],
        producto["categoria"],
        producto.get("subcategoria"),
        producto.get("potencia_hp", 0),
        producto.get("precio", 0),
        producto.get("stock", 0),
        producto.get("stock_minimo", 0),
        bool_a_int(producto.get("instalable", False)),
        bool_a_int(producto.get("equipo_critico", False)),
        bool_a_int(producto.get("requiere_mantenimiento", False)),
        bool_a_int(producto.get("precio_variable", False)),
        bool_a_int(producto.get("control_stock", True)),
        bool_a_int(producto.get("requiere_diseno_tecnico", False))
    ))

# ============================================================
# CARGAR SERVICIOS
# ============================================================

servicios = cargar_json("servicios.json")

for servicio in servicios:
    cursor.execute("""
    INSERT OR REPLACE INTO servicios (
        id_servicio,
        nombre,
        tipo_servicio,
        costo_base,
        duracion_dias_base,
        nivel_validacion,
        considera_ultimo_servicio,
        requiere_revision_previa,
        observaciones_base
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        servicio["id_servicio"],
        servicio["nombre"],
        servicio["tipo_servicio"],
        servicio.get("costo_base", 0),
        servicio.get("duracion_dias_base", 1),
        servicio["nivel_validacion"],
        bool_a_int(servicio.get("considera_ultimo_servicio", False)),
        bool_a_int(servicio.get("requiere_revision_previa", False)),
        lista_a_json_texto(servicio.get("observaciones_base", []))
    ))

# ============================================================
# CARGAR REGLAS DE INFERENCIA
# ============================================================

reglas = cargar_json("reglas_inferencia.json")

for regla in reglas:
    cursor.execute("""
    INSERT OR REPLACE INTO reglas_inferencia (
        id_regla,
        nombre,
        categoria,
        prioridad,
        agente_responsable,
        condiciones,
        acciones,
        explicacion
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        regla["id_regla"],
        regla["nombre"],
        regla["categoria"],
        regla["prioridad"],
        regla["agente_responsable"],
        lista_a_json_texto(regla.get("condiciones", [])),
        lista_a_json_texto(regla.get("acciones", [])),
        regla.get("explicacion")
    ))

# ============================================================
# CARGAR ALIAS DE PRODUCTOS
# Se eliminan antes para evitar duplicados al recargar datos.
# ============================================================

cursor.execute("DELETE FROM alias_productos")

alias_productos = cargar_json("alias_productos.json")

for grupo_alias in alias_productos:
    for alias in grupo_alias.get("alias", []):
        cursor.execute("""
        INSERT INTO alias_productos (
            id_producto,
            nombre_producto,
            alias
        ) VALUES (?, ?, ?)
        """, (
            grupo_alias["id_producto"],
            grupo_alias["nombre_producto"],
            alias
        ))

# ============================================================
# CARGAR USUARIOS INTERNOS
# ============================================================

usuarios = cargar_json("usuarios_internos.json")

for usuario in usuarios:
    cursor.execute("""
    INSERT OR REPLACE INTO usuarios_internos (
        id_usuario,
        nombre,
        rol,
        nivel_validacion,
        puede_validar,
        puede_autorizar_servicios,
        requiere_supervision_tecnica
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        usuario["id_usuario"],
        usuario["nombre"],
        usuario["rol"],
        usuario["nivel_validacion"],
        lista_a_json_texto(usuario.get("puede_validar", [])),
        lista_a_json_texto(usuario.get("puede_autorizar_servicios", [])),
        bool_a_int(usuario.get("requiere_supervision_tecnica", False))
    ))

conexion.commit()
conexion.close()

print("Datos cargados correctamente en la base de datos.")
