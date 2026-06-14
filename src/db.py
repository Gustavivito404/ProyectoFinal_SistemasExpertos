import json
import os
import sqlite3
import unicodedata
from typing import Any, Dict, List, Optional


# ============================================================
# db.py
# Capa de acceso a datos para FireGuard Expert.
#
# Este archivo evita repetir consultas SQL dentro de los agentes
# e incluye funciones operativas para:
# - clientes preliminares
# - solicitudes de servicio
# - validaciones
# - movimientos de inventario
# - historial del chat público
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(BASE_DIR, "bd", "sistema_incendio.db")


# ============================================================
# UTILIDADES GENERALES
# ============================================================

def conectar() -> sqlite3.Connection:
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def fila_a_dict(fila: sqlite3.Row) -> Dict[str, Any]:
    return dict(fila) if fila is not None else {}


def filas_a_lista(filas: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [dict(fila) for fila in filas]


def texto_normalizado(texto: str) -> str:
    if texto is None:
        return ""

    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")
    texto = " ".join(texto.split())
    return texto


def json_a_lista(valor: Optional[str]) -> List[Any]:
    if not valor:
        return []

    try:
        return json.loads(valor)
    except json.JSONDecodeError:
        return []


def json_a_dict(valor: Optional[str]) -> Dict[str, Any]:
    if not valor:
        return {}

    try:
        data = json.loads(valor)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def a_json_texto(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False)


def bool_a_int(valor: Any) -> int:
    return 1 if bool(valor) else 0


def reconstruir_cliente(cliente: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte el cliente plano de SQLite a la estructura que esperan los agentes.
    """
    if not cliente:
        return {}

    cliente = dict(cliente)

    cliente["cliente_frecuente"] = bool(cliente.get("cliente_frecuente"))
    cliente["equipo_instalado"] = {
        "bomba_electrica": bool(cliente.get("bomba_electrica")),
        "bomba_piloto": bool(cliente.get("bomba_piloto")),
        "bomba_combustion": bool(cliente.get("bomba_combustion")),
        "tablero_control_propio": bool(cliente.get("tablero_control_propio")),
    }
    cliente["facturacion"] = {
        "rfc": cliente.get("rfc"),
        "direccion": cliente.get("direccion"),
    }

    return cliente


def reconstruir_servicio(servicio: Dict[str, Any]) -> Dict[str, Any]:
    if not servicio:
        return {}

    servicio = dict(servicio)
    servicio["considera_ultimo_servicio"] = bool(servicio.get("considera_ultimo_servicio"))
    servicio["requiere_revision_previa"] = bool(servicio.get("requiere_revision_previa"))
    servicio["observaciones_base"] = json_a_lista(servicio.get("observaciones_base"))
    return servicio


def reconstruir_usuario(usuario: Dict[str, Any]) -> Dict[str, Any]:
    if not usuario:
        return {}

    usuario = dict(usuario)
    usuario["puede_validar"] = json_a_lista(usuario.get("puede_validar"))
    usuario["puede_autorizar_servicios"] = json_a_lista(usuario.get("puede_autorizar_servicios"))
    usuario["requiere_supervision_tecnica"] = bool(usuario.get("requiere_supervision_tecnica"))
    return usuario


# ============================================================
# CONSULTAS GENERALES
# ============================================================

def obtener_clientes() -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("SELECT * FROM clientes ORDER BY id_cliente").fetchall()
    return [reconstruir_cliente(fila_a_dict(fila)) for fila in filas]


def obtener_productos() -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("SELECT * FROM productos ORDER BY id_producto").fetchall()
    return filas_a_lista(filas)


def obtener_servicios() -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("SELECT * FROM servicios ORDER BY id_servicio").fetchall()
    return [reconstruir_servicio(fila_a_dict(fila)) for fila in filas]


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
    return [reconstruir_usuario(fila_a_dict(fila)) for fila in filas]


# ============================================================
# LOGIN
# ============================================================

def verificar_credenciales(id_usuario: str, contrasena: str) -> Optional[Dict[str, Any]]:
    with conectar() as conexion:
        fila = conexion.execute("""
            SELECT id_usuario, nombre, rol, nivel_validacion
            FROM usuarios_internos
            WHERE id_usuario = ? AND contrasena = ?
        """, (id_usuario, contrasena)).fetchone()

    return fila_a_dict(fila) if fila else None


# ============================================================
# BÚSQUEDAS PARA AGENTES
# ============================================================

def buscar_cliente_por_id(id_cliente: str) -> Optional[Dict[str, Any]]:
    with conectar() as conexion:
        fila = conexion.execute(
            "SELECT * FROM clientes WHERE id_cliente = ?",
            (id_cliente,)
        ).fetchone()

    return reconstruir_cliente(fila_a_dict(fila)) if fila else None


def buscar_cliente_en_texto(texto: str) -> Optional[Dict[str, Any]]:
    texto_norm = texto_normalizado(texto)

    for cliente in obtener_clientes():
        id_norm = texto_normalizado(cliente["id_cliente"])
        nombre_norm = texto_normalizado(cliente["nombre"])

        if id_norm in texto_norm or nombre_norm in texto_norm:
            return cliente

    return None


def buscar_productos_en_texto(texto: str) -> List[Dict[str, Any]]:
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
            "problema",
            "dano",
            "daño"
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
        if any(texto_normalizado(palabra) in texto_norm for palabra in palabras):
            return obtener_servicio_por_tipo(tipo)

    return None


# ============================================================
# CLIENTES PRELIMINARES
# ============================================================

def crear_cliente_preliminar(
    nombre: Optional[str] = None,
    tipo: Optional[str] = None,
    rfc: Optional[str] = None,
    direccion: Optional[str] = None,
    bomba_electrica: bool = False,
    bomba_piloto: bool = False,
    bomba_combustion: bool = False,
    tablero_control_propio: bool = False,
    observaciones: Optional[str] = None
) -> int:
    with conectar() as conexion:
        cursor = conexion.execute("""
            INSERT INTO clientes_preliminares (
                nombre, tipo, rfc, direccion,
                bomba_electrica, bomba_piloto, bomba_combustion, tablero_control_propio,
                observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nombre,
            tipo,
            rfc,
            direccion,
            bool_a_int(bomba_electrica),
            bool_a_int(bomba_piloto),
            bool_a_int(bomba_combustion),
            bool_a_int(tablero_control_propio),
            observaciones
        ))
        conexion.commit()
        return int(cursor.lastrowid)


def listar_clientes_preliminares(estado: Optional[str] = None) -> List[Dict[str, Any]]:
    with conectar() as conexion:
        if estado:
            filas = conexion.execute("""
                SELECT * FROM clientes_preliminares
                WHERE estado = ?
                ORDER BY fecha_registro DESC
            """, (estado,)).fetchall()
        else:
            filas = conexion.execute("""
                SELECT * FROM clientes_preliminares
                ORDER BY fecha_registro DESC
            """).fetchall()

    return filas_a_lista(filas)


def obtener_cliente_preliminar(id_preliminar: int) -> Optional[Dict[str, Any]]:
    with conectar() as conexion:
        fila = conexion.execute("""
            SELECT * FROM clientes_preliminares
            WHERE id_preliminar = ?
        """, (id_preliminar,)).fetchone()

    return fila_a_dict(fila) if fila else None


def actualizar_estado_cliente_preliminar(
    id_preliminar: int,
    estado: str,
    id_usuario_validador: Optional[str] = None,
    observaciones: Optional[str] = None
) -> None:
    with conectar() as conexion:
        conexion.execute("""
            UPDATE clientes_preliminares
            SET estado = ?,
                id_usuario_validador = COALESCE(?, id_usuario_validador),
                observaciones = COALESCE(?, observaciones),
                fecha_validacion = CURRENT_TIMESTAMP
            WHERE id_preliminar = ?
        """, (estado, id_usuario_validador, observaciones, id_preliminar))
        conexion.commit()


def generar_nuevo_id_cliente() -> str:
    """
    Genera IDs C001, C002, C003...
    """
    with conectar() as conexion:
        fila = conexion.execute("""
            SELECT id_cliente FROM clientes
            WHERE id_cliente LIKE 'C%'
            ORDER BY id_cliente DESC
            LIMIT 1
        """).fetchone()

    if not fila:
        return "C001"

    ultimo = str(fila["id_cliente"]).replace("C", "")

    try:
        siguiente = int(ultimo) + 1
    except ValueError:
        siguiente = 1

    return f"C{siguiente:03d}"


def convertir_cliente_preliminar_a_cliente(
    id_preliminar: int,
    id_usuario_validador: Optional[str] = None
) -> Optional[str]:
    preliminar = obtener_cliente_preliminar(id_preliminar)

    if not preliminar:
        return None

    nuevo_id = generar_nuevo_id_cliente()

    with conectar() as conexion:
        conexion.execute("""
            INSERT INTO clientes (
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
            ) VALUES (?, ?, ?, 0, 0, NULL, ?, ?, ?, ?, ?, ?)
        """, (
            nuevo_id,
            preliminar.get("nombre"),
            preliminar.get("tipo") or "Comercial",
            preliminar.get("bomba_electrica", 0),
            preliminar.get("bomba_piloto", 0),
            preliminar.get("bomba_combustion", 0),
            preliminar.get("tablero_control_propio", 0),
            preliminar.get("rfc"),
            preliminar.get("direccion")
        ))

        conexion.execute("""
            UPDATE clientes_preliminares
            SET estado = 'convertido_a_cliente',
                fecha_validacion = CURRENT_TIMESTAMP,
                id_usuario_validador = ?,
                id_cliente_generado = ?
            WHERE id_preliminar = ?
        """, (id_usuario_validador, nuevo_id, id_preliminar))

        conexion.commit()

    return nuevo_id


# ============================================================
# PEDIDOS DE PRODUCTOS
# ============================================================

def crear_pedido_productos(
    id_cliente: Optional[str],
    productos: List[Dict[str, Any]],
    total: float,
    resumen: Optional[str] = None,
    tipo_pedido: str = "cotizacion",
    estado: str = "pendiente_validacion"
) -> int:
    with conectar() as conexion:
        cursor = conexion.execute("""
            INSERT INTO pedidos (
                id_cliente, tipo_pedido, total, estado, resumen
            ) VALUES (?, ?, ?, ?, ?)
        """, (id_cliente, tipo_pedido, total, estado, resumen))

        id_pedido = int(cursor.lastrowid)

        for producto in productos:
            conexion.execute("""
                INSERT INTO detalle_pedidos (
                    id_pedido, id_producto, cantidad, precio_unitario, subtotal
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                id_pedido,
                producto["id_producto"],
                int(producto.get("cantidad", 1)),
                float(producto.get("precio", 0)),
                float(producto.get("subtotal", 0))
            ))

        conexion.commit()
        return id_pedido


def listar_pedidos(estado: Optional[str] = None) -> List[Dict[str, Any]]:
    with conectar() as conexion:
        if estado:
            filas = conexion.execute("""
                SELECT p.*, c.nombre AS nombre_cliente
                FROM pedidos p
                LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
                WHERE p.estado = ?
                ORDER BY p.fecha DESC
            """, (estado,)).fetchall()
        else:
            filas = conexion.execute("""
                SELECT p.*, c.nombre AS nombre_cliente
                FROM pedidos p
                LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
                ORDER BY p.fecha DESC
            """).fetchall()

    return filas_a_lista(filas)


# ============================================================
# SOLICITUDES DE SERVICIO
# ============================================================

def crear_solicitud_servicio(
    id_cliente: Optional[str],
    id_servicio: str,
    mensaje_original: Optional[str] = None,
    descripcion_cliente: Optional[str] = None,
    ubicacion_servicio: Optional[str] = None,
    servicio_foraneo: bool = False,
    costo_base: float = 0,
    costo_extra_distancia: float = 0,
    duracion_dias_base: int = 1,
    nivel_validacion: Optional[str] = None,
    requiere_revision_previa: bool = False,
    resumen_supervisor: Optional[str] = None,
    reglas_activadas: Optional[List[Dict[str, Any]]] = None,
    advertencias: Optional[List[str]] = None,
    recomendaciones: Optional[List[str]] = None,
    observaciones_logistica: Optional[str] = None,
    estado: str = "pendiente_validacion",
    id_cliente_preliminar: Optional[int] = None,
    id_usuario_creador: Optional[str] = None
) -> int:
    total_estimado = float(costo_base) + float(costo_extra_distancia)

    with conectar() as conexion:
        cursor = conexion.execute("""
            INSERT INTO solicitudes_servicio (
                id_cliente,
                id_cliente_preliminar,
                id_servicio,
                mensaje_original,
                descripcion_cliente,
                ubicacion_servicio,
                servicio_foraneo,
                costo_base,
                costo_extra_distancia,
                total_estimado,
                duracion_dias_base,
                nivel_validacion,
                requiere_revision_previa,
                estado,
                resumen_supervisor,
                reglas_activadas,
                advertencias,
                recomendaciones,
                observaciones_logistica,
                id_usuario_creador
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_cliente,
            id_cliente_preliminar,
            id_servicio,
            mensaje_original,
            descripcion_cliente,
            ubicacion_servicio,
            bool_a_int(servicio_foraneo),
            float(costo_base),
            float(costo_extra_distancia),
            total_estimado,
            int(duracion_dias_base),
            nivel_validacion,
            bool_a_int(requiere_revision_previa),
            estado,
            resumen_supervisor,
            a_json_texto(reglas_activadas or []),
            a_json_texto(advertencias or []),
            a_json_texto(recomendaciones or []),
            observaciones_logistica,
            id_usuario_creador
        ))
        conexion.commit()
        return int(cursor.lastrowid)


def crear_solicitud_desde_resultado(
    resultado_motor: Dict[str, Any],
    resumen_supervisor: Optional[Dict[str, Any]] = None,
    id_usuario_creador: Optional[str] = None,
    costo_extra_distancia: float = 0,
    observaciones_logistica: Optional[str] = None
) -> Optional[int]:
    servicio = resultado_motor.get("servicio")

    if not servicio:
        return None

    cliente = resultado_motor.get("cliente")
    id_cliente = cliente.get("id_cliente") if cliente else None

    resumen_texto = None
    if resumen_supervisor:
        resumen_texto = resumen_supervisor.get("resumen_solicitud") or str(resumen_supervisor)

    estado = resultado_motor.get("estado", "pendiente_validacion")

    return crear_solicitud_servicio(
        id_cliente=id_cliente,
        id_servicio=servicio["id_servicio"],
        mensaje_original=resultado_motor.get("mensaje_original"),
        descripcion_cliente=resultado_motor.get("mensaje_original"),
        servicio_foraneo=bool(resultado_motor.get("servicio_foraneo")),
        costo_base=float(resultado_motor.get("costo_servicio_base", 0)),
        costo_extra_distancia=float(costo_extra_distancia),
        duracion_dias_base=int(resultado_motor.get("duracion_dias_base", 1)),
        nivel_validacion=servicio.get("nivel_validacion"),
        requiere_revision_previa=bool(servicio.get("requiere_revision_previa")),
        resumen_supervisor=resumen_texto,
        reglas_activadas=resultado_motor.get("reglas_activadas", []),
        advertencias=resultado_motor.get("advertencias", []),
        recomendaciones=resultado_motor.get("recomendaciones", []),
        observaciones_logistica=observaciones_logistica,
        estado=estado,
        id_usuario_creador=id_usuario_creador
    )


def listar_solicitudes_servicio(
    estado: Optional[str] = None,
    nivel_validacion: Optional[str] = None
) -> List[Dict[str, Any]]:
    consulta = """
        SELECT
            s.*,
            c.nombre AS nombre_cliente,
            cp.nombre AS nombre_cliente_preliminar,
            sv.nombre AS nombre_servicio,
            sv.tipo_servicio
        FROM solicitudes_servicio s
        LEFT JOIN clientes c ON s.id_cliente = c.id_cliente
        LEFT JOIN clientes_preliminares cp ON s.id_cliente_preliminar = cp.id_preliminar
        INNER JOIN servicios sv ON s.id_servicio = sv.id_servicio
        WHERE 1 = 1
    """
    parametros: List[Any] = []

    if estado:
        consulta += " AND s.estado = ?"
        parametros.append(estado)

    if nivel_validacion:
        consulta += " AND s.nivel_validacion = ?"
        parametros.append(nivel_validacion)

    consulta += " ORDER BY s.fecha DESC"

    with conectar() as conexion:
        filas = conexion.execute(consulta, parametros).fetchall()

    solicitudes = filas_a_lista(filas)

    for solicitud in solicitudes:
        solicitud["reglas_activadas"] = json_a_lista(solicitud.get("reglas_activadas"))
        solicitud["advertencias"] = json_a_lista(solicitud.get("advertencias"))
        solicitud["recomendaciones"] = json_a_lista(solicitud.get("recomendaciones"))

    return solicitudes


def obtener_solicitud_servicio(id_solicitud: int) -> Optional[Dict[str, Any]]:
    with conectar() as conexion:
        fila = conexion.execute("""
            SELECT
                s.*,
                c.nombre AS nombre_cliente,
                cp.nombre AS nombre_cliente_preliminar,
                sv.nombre AS nombre_servicio,
                sv.tipo_servicio
            FROM solicitudes_servicio s
            LEFT JOIN clientes c ON s.id_cliente = c.id_cliente
            LEFT JOIN clientes_preliminares cp ON s.id_cliente_preliminar = cp.id_preliminar
            INNER JOIN servicios sv ON s.id_servicio = sv.id_servicio
            WHERE s.id_solicitud = ?
        """, (id_solicitud,)).fetchone()

    if not fila:
        return None

    solicitud = fila_a_dict(fila)
    solicitud["reglas_activadas"] = json_a_lista(solicitud.get("reglas_activadas"))
    solicitud["advertencias"] = json_a_lista(solicitud.get("advertencias"))
    solicitud["recomendaciones"] = json_a_lista(solicitud.get("recomendaciones"))
    return solicitud


def actualizar_estado_solicitud(
    id_solicitud: int,
    estado: str,
    id_usuario_validador: Optional[str] = None
) -> None:
    with conectar() as conexion:
        conexion.execute("""
            UPDATE solicitudes_servicio
            SET estado = ?,
                id_usuario_validador = COALESCE(?, id_usuario_validador),
                fecha_validacion = CASE
                    WHEN ? IS NOT NULL THEN CURRENT_TIMESTAMP
                    ELSE fecha_validacion
                END
            WHERE id_solicitud = ?
        """, (estado, id_usuario_validador, id_usuario_validador, id_solicitud))
        conexion.commit()


def validar_solicitud_servicio(
    id_solicitud: int,
    id_usuario: Optional[str],
    decision: str,
    comentarios: Optional[str] = None,
    costo_extra_distancia: float = 0,
    nueva_duracion_dias: Optional[int] = None
) -> int:
    solicitud = obtener_solicitud_servicio(id_solicitud)

    if not solicitud:
        raise ValueError("No se encontró la solicitud de servicio.")

    total_estimado = float(solicitud.get("costo_base", 0)) + float(costo_extra_distancia)

    mapa_estados = {
        "aprobar": "aprobada",
        "rechazar": "rechazada",
        "mas_info": "solicitar_mas_informacion",
        "pendiente": "pendiente_validacion"
    }

    nuevo_estado = mapa_estados.get(decision, decision)

    with conectar() as conexion:
        cursor = conexion.execute("""
            INSERT INTO validaciones_servicio (
                id_solicitud,
                id_usuario,
                decision,
                comentarios,
                costo_extra_distancia,
                total_estimado,
                nueva_duracion_dias
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            id_solicitud,
            id_usuario,
            decision,
            comentarios,
            float(costo_extra_distancia),
            total_estimado,
            nueva_duracion_dias
        ))

        conexion.execute("""
            UPDATE solicitudes_servicio
            SET estado = ?,
                costo_extra_distancia = ?,
                total_estimado = ?,
                duracion_dias_base = COALESCE(?, duracion_dias_base),
                observaciones_logistica = COALESCE(?, observaciones_logistica),
                id_usuario_validador = ?,
                fecha_validacion = CURRENT_TIMESTAMP
            WHERE id_solicitud = ?
        """, (
            nuevo_estado,
            float(costo_extra_distancia),
            total_estimado,
            nueva_duracion_dias,
            comentarios,
            id_usuario,
            id_solicitud
        ))

        conexion.commit()
        return int(cursor.lastrowid)


# ============================================================
# INVENTARIO
# ============================================================

def obtener_producto_por_id(id_producto: str) -> Optional[Dict[str, Any]]:
    with conectar() as conexion:
        fila = conexion.execute("""
            SELECT * FROM productos WHERE id_producto = ?
        """, (id_producto,)).fetchone()

    return fila_a_dict(fila) if fila else None


def registrar_movimiento_inventario(
    id_producto: str,
    tipo_movimiento: str,
    cantidad: int,
    motivo: Optional[str] = None,
    id_usuario: Optional[str] = None
) -> int:
    producto = obtener_producto_por_id(id_producto)

    if not producto:
        raise ValueError("No se encontró el producto.")

    if not bool(producto.get("control_stock", 1)):
        raise ValueError("El producto no maneja control de stock automático.")

    cantidad = int(cantidad)
    stock_anterior = int(producto.get("stock", 0))

    if tipo_movimiento in ["venta", "uso_en_servicio", "salida"]:
        stock_nuevo = stock_anterior - cantidad
    elif tipo_movimiento in ["reabastecimiento", "entrada"]:
        stock_nuevo = stock_anterior + cantidad
    elif tipo_movimiento == "ajuste_manual":
        stock_nuevo = cantidad
    else:
        raise ValueError("Tipo de movimiento no reconocido.")

    if stock_nuevo < 0:
        raise ValueError("El movimiento dejaría el stock en negativo.")

    with conectar() as conexion:
        cursor = conexion.execute("""
            INSERT INTO movimientos_inventario (
                id_producto,
                tipo_movimiento,
                cantidad,
                stock_anterior,
                stock_nuevo,
                motivo,
                id_usuario
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            id_producto,
            tipo_movimiento,
            cantidad,
            stock_anterior,
            stock_nuevo,
            motivo,
            id_usuario
        ))

        conexion.execute("""
            UPDATE productos
            SET stock = ?
            WHERE id_producto = ?
        """, (stock_nuevo, id_producto))

        conexion.commit()
        return int(cursor.lastrowid)


def listar_movimientos_inventario() -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("""
            SELECT
                m.*,
                p.nombre AS nombre_producto,
                u.nombre AS nombre_usuario
            FROM movimientos_inventario m
            INNER JOIN productos p ON m.id_producto = p.id_producto
            LEFT JOIN usuarios_internos u ON m.id_usuario = u.id_usuario
            ORDER BY m.fecha DESC
        """).fetchall()

    return filas_a_lista(filas)


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


# ============================================================
# CHAT PÚBLICO
# ============================================================

def iniciar_conversacion_cliente() -> int:
    with conectar() as conexion:
        cursor = conexion.execute("""
            INSERT INTO conversaciones_cliente DEFAULT VALUES
        """)
        conexion.commit()
        return int(cursor.lastrowid)


def guardar_mensaje_chat(
    id_conversacion: int,
    remitente: str,
    mensaje: str
) -> int:
    with conectar() as conexion:
        cursor = conexion.execute("""
            INSERT INTO mensajes_chat_cliente (
                id_conversacion,
                remitente,
                mensaje
            ) VALUES (?, ?, ?)
        """, (id_conversacion, remitente, mensaje))

        conexion.execute("""
            UPDATE conversaciones_cliente
            SET fecha_ultima_interaccion = CURRENT_TIMESTAMP
            WHERE id_conversacion = ?
        """, (id_conversacion,))

        conexion.commit()
        return int(cursor.lastrowid)


def actualizar_conversacion_cliente(
    id_conversacion: int,
    estado: Optional[str] = None,
    intencion_detectada: Optional[str] = None,
    id_cliente: Optional[str] = None,
    id_cliente_preliminar: Optional[int] = None,
    id_solicitud: Optional[int] = None
) -> None:
    with conectar() as conexion:
        conexion.execute("""
            UPDATE conversaciones_cliente
            SET estado = COALESCE(?, estado),
                intencion_detectada = COALESCE(?, intencion_detectada),
                id_cliente = COALESCE(?, id_cliente),
                id_cliente_preliminar = COALESCE(?, id_cliente_preliminar),
                id_solicitud = COALESCE(?, id_solicitud),
                fecha_ultima_interaccion = CURRENT_TIMESTAMP
            WHERE id_conversacion = ?
        """, (
            estado,
            intencion_detectada,
            id_cliente,
            id_cliente_preliminar,
            id_solicitud,
            id_conversacion
        ))
        conexion.commit()


def obtener_mensajes_conversacion(id_conversacion: int) -> List[Dict[str, Any]]:
    with conectar() as conexion:
        filas = conexion.execute("""
            SELECT * FROM mensajes_chat_cliente
            WHERE id_conversacion = ?
            ORDER BY fecha ASC, id_mensaje ASC
        """, (id_conversacion,)).fetchall()

    return filas_a_lista(filas)


def listar_conversaciones_cliente(estado: Optional[str] = None) -> List[Dict[str, Any]]:
    with conectar() as conexion:
        if estado:
            filas = conexion.execute("""
                SELECT * FROM conversaciones_cliente
                WHERE estado = ?
                ORDER BY fecha_ultima_interaccion DESC
            """, (estado,)).fetchall()
        else:
            filas = conexion.execute("""
                SELECT * FROM conversaciones_cliente
                ORDER BY fecha_ultima_interaccion DESC
            """).fetchall()

    return filas_a_lista(filas)
