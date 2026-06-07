import json
import os
import sqlite3
import unicodedata
from typing import Any, Dict, List, Optional


# ============================================================
# db.py
# Capa de acceso a datos para el sistema experto contra incendio.
#
# Este archivo evita repetir consultas SQL dentro de los agentes.
# Recomendación:
#   - Guardar este archivo en: src/db.py
#   - Ejecutar desde la raíz del proyecto.
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(BASE_DIR, "bd", "sistema_incendio.db")


def conectar() -> sqlite3.Connection:
    """Crea una conexión a SQLite con filas tipo diccionario."""
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def fila_a_dict(fila: sqlite3.Row) -> Dict[str, Any]:
    return dict(fila) if fila is not None else {}


def filas_a_lista(filas: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [dict(fila) for fila in filas]


def texto_normalizado(texto: str) -> str:
    """
    Convierte texto a una forma más fácil de comparar:
    - minúsculas
    - sin acentos
    - sin espacios duplicados
    """
    if texto is None:
        return ""

    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")
    texto = " ".join(texto.split())
    return texto


def json_a_lista(valor: Optional[str]) -> List[Any]:
    """Convierte texto JSON guardado en SQLite a lista de Python."""
    if not valor:
        return []

    try:
        return json.loads(valor)
    except json.JSONDecodeError:
        return []


# ============================================================
# CONSULTAS GENERALES
# ============================================================

def obtener_clientes() -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("SELECT * FROM clientes ORDER BY id_cliente").fetchall()
    return filas_a_lista(filas)


def obtener_productos() -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("SELECT * FROM productos ORDER BY id_producto").fetchall()
    return filas_a_lista(filas)


def obtener_servicios() -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("SELECT * FROM servicios ORDER BY id_servicio").fetchall()

    servicios = filas_a_lista(filas)

    for servicio in servicios:
        servicio["observaciones_base"] = json_a_lista(servicio.get("observaciones_base"))

    return servicios


def obtener_reglas() -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("SELECT * FROM reglas_inferencia ORDER BY id_regla").fetchall()

    reglas = filas_a_lista(filas)

    for regla in reglas:
        regla["condiciones"] = json_a_lista(regla.get("condiciones"))
        regla["acciones"] = json_a_lista(regla.get("acciones"))

    return reglas


def obtener_alias_productos() -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("""
            SELECT
                alias_productos.id_producto,
                alias_productos.nombre_producto,
                alias_productos.alias,
                productos.nombre,
                productos.categoria,
                productos.subcategoria,
                productos.precio,
                productos.stock,
                productos.stock_minimo,
                productos.instalable,
                productos.equipo_critico,
                productos.control_stock,
                productos.precio_variable,
                productos.requiere_diseno_tecnico
            FROM alias_productos
            INNER JOIN productos
                ON alias_productos.id_producto = productos.id_producto
            ORDER BY LENGTH(alias_productos.alias) DESC
        """).fetchall()

    return filas_a_lista(filas)


def obtener_usuarios_internos() -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("SELECT * FROM usuarios_internos ORDER BY id_usuario").fetchall()

    usuarios = filas_a_lista(filas)

    for usuario in usuarios:
        usuario["puede_validar"] = json_a_lista(usuario.get("puede_validar"))
        usuario["puede_autorizar_servicios"] = json_a_lista(usuario.get("puede_autorizar_servicios"))

    return usuarios


# ============================================================
# BÚSQUEDAS PARA AGENTES
# ============================================================

def buscar_cliente_por_id(id_cliente: str) -> Optional[Dict[str, Any]]:
    with conectar() as conexion:
        fila = conexion.execute(
            "SELECT * FROM clientes WHERE id_cliente = ?",
            (id_cliente,)
        ).fetchone()

    return fila_a_dict(fila) if fila else None


def buscar_cliente_en_texto(texto: str) -> Optional[Dict[str, Any]]:
    """
    Busca si el mensaje contiene el nombre o ID de un cliente registrado.
    """
    texto_norm = texto_normalizado(texto)

    for cliente in obtener_clientes():
        id_norm = texto_normalizado(cliente["id_cliente"])
        nombre_norm = texto_normalizado(cliente["nombre"])

        if id_norm in texto_norm or nombre_norm in texto_norm:
            return cliente

    return None


def buscar_productos_en_texto(texto: str) -> List[Dict[str, Any]]:
    """
    Busca productos mencionados en el mensaje usando alias_productos.
    Regresa productos únicos.
    """
    texto_norm = texto_normalizado(texto)
    encontrados: Dict[str, Dict[str, Any]] = {}

    for item in obtener_alias_productos():
        alias_norm = texto_normalizado(item["alias"])

        if alias_norm and alias_norm in texto_norm:
            id_producto = item["id_producto"]

            if id_producto not in encontrados:
                encontrados[id_producto] = item

    return list(encontrados.values())


def obtener_servicio_por_tipo(tipo_servicio: str) -> Optional[Dict[str, Any]]:
    tipo_norm = texto_normalizado(tipo_servicio)

    for servicio in obtener_servicios():
        if texto_normalizado(servicio["tipo_servicio"]) == tipo_norm:
            return servicio

    return None


def buscar_servicio_en_texto(texto: str) -> Optional[Dict[str, Any]]:
    """
    Detecta un servicio con palabras clave básicas.
    Si el mensaje solo dice "mantenimiento", no se fuerza preventivo/correctivo.
    """
    texto_norm = texto_normalizado(texto)

    mapa_servicios = [
        ("Correctivo", [
            "correctivo",
            "falla",
            "fallando",
            "no funciona",
            "no prende",
            "no arranca",
            "reparar",
            "reparacion",
            "fuga",
            "goteo",
            "problema"
        ]),
        ("Preventivo", [
            "preventivo",
            "mantenimiento preventivo",
            "servicio preventivo",
            "revision periodica"
        ]),
        ("Inspeccion", [
            "inspeccion",
            "inspeccionar",
            "revision sencilla",
            "revision general",
            "revisar sistema",
            "checar sistema"
        ]),
        ("Instalacion", [
            "instalacion",
            "instalar",
            "montaje",
            "nuevo sistema",
            "colocar sistema"
        ])
    ]

    for tipo, palabras in mapa_servicios:
        if any(palabra in texto_norm for palabra in palabras):
            return obtener_servicio_por_tipo(tipo)

    return None


# ============================================================
# HISTORIAL DE INFERENCIAS
# ============================================================

def guardar_inferencia(
    tipo_operacion: str,
    resultado: str,
    id_operacion: Optional[int] = None,
    id_regla: Optional[str] = None,
    mensaje_original: Optional[str] = None,
    intencion_detectada: Optional[str] = None,
    condicion_evaluada: Optional[str] = None,
    accion_realizada: Optional[str] = None,
    explicacion: Optional[str] = None
) -> int:
    """
    Guarda una inferencia o evento explicable en la tabla inferencias.
    Regresa el ID generado.
    """
    with conectar() as conexion:
        cursor = conexion.execute("""
            INSERT INTO inferencias (
                tipo_operacion,
                id_operacion,
                id_regla,
                mensaje_original,
                intencion_detectada,
                condicion_evaluada,
                accion_realizada,
                resultado,
                explicacion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tipo_operacion,
            id_operacion,
            id_regla,
            mensaje_original,
            intencion_detectada,
            condicion_evaluada,
            accion_realizada,
            resultado,
            explicacion
        ))

        conexion.commit()
        return int(cursor.lastrowid)
