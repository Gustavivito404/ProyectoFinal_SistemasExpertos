import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st


# ============================================================
# app.py - Interfaz Streamlit para FireGuard Expert
#
# Ejecutar desde la raíz del proyecto:
#   py -m streamlit run app.py
#
# Estructura esperada:
# Proyecto/
# ├── app.py
# ├── bd/
# │   └── sistema_incendio.db
# └── src/
#     ├── db.py
#     ├── agente_cliente.py
#     ├── motor_inferencia.py
#     └── agente_supervisor.py
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

try:
    import db
    from agente_cliente import AgenteAtencionCliente
    from motor_inferencia import MotorInferencia
    from agente_supervisor import AgenteSupervisor
except Exception as error:
    st.set_page_config(page_title="FireGuard Expert", layout="wide")
    st.error("No se pudieron importar los módulos del sistema.")
    st.write("Revisa que `db.py`, `agente_cliente.py`, `motor_inferencia.py` y `agente_supervisor.py` estén dentro de la carpeta `src/`.")
    st.exception(error)
    st.stop()


# ============================================================
# CONFIGURACIÓN VISUAL
# ============================================================

st.set_page_config(
    page_title="FireGuard Expert",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }

    .fireguard-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #b91c1c;
        margin-bottom: 0;
    }

    .fireguard-subtitle {
        font-size: 1rem;
        color: #4b5563;
        margin-top: 0.2rem;
        margin-bottom: 1.2rem;
    }

    .card {
        background: white;
        border-radius: 14px;
        padding: 1.1rem;
        box-shadow: 0 3px 12px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }

    .warning-box {
        background-color: #fff7ed;
        border-left: 5px solid #f97316;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.6rem;
    }

    .ok-box {
        background-color: #f0fdf4;
        border-left: 5px solid #22c55e;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.6rem;
    }

    .danger-box {
        background-color: #fef2f2;
        border-left: 5px solid #dc2626;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.6rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def safe_call(func, default):
    try:
        return func()
    except Exception:
        return default


def to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def show_header(title: str, subtitle: str = ""):
    st.markdown(f"<h1 class='fireguard-title'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p class='fireguard-subtitle'>{subtitle}</p>", unsafe_allow_html=True)


def render_list(items: List[str], empty_message: str = "Sin elementos."):
    if not items:
        st.write(empty_message)
        return
    for item in items:
        st.markdown(f"- {item}")


def compact_json(data: Any):
    st.json(data, expanded=False)


def consultar_tabla(nombre_tabla: str) -> pd.DataFrame:
    try:
        with db.conectar() as conexion:
            return pd.read_sql_query(f"SELECT * FROM {nombre_tabla}", conexion)
    except Exception:
        return pd.DataFrame()


# ============================================================
# INICIALIZAR AGENTES
# ============================================================

agente_1 = AgenteAtencionCliente()
motor = MotorInferencia(guardar_historial=False)
supervisor = AgenteSupervisor()


# ============================================================
# GESTIÓN DE SESIÓN (LOGIN)
# ============================================================

if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = None
    st.session_state["rol"] = None

st.sidebar.markdown("## 🔥 FireGuard Expert")
st.sidebar.caption("Sistema experto multiagente contra incendio")
st.sidebar.markdown("---")

# Panel de Login
st.sidebar.markdown("### 🔐 Acceso Interno")
if st.session_state["usuario_actual"] is None:
    user_input = st.sidebar.text_input("ID Usuario", placeholder="Ej. U004")
    pass_input = st.sidebar.text_input("Contraseña", type="password")
    
    if st.sidebar.button("Iniciar Sesión", type="primary", use_container_width=True):
        # Llama a la función que agregaremos en db.py
        user_data = db.verificar_credenciales(user_input, pass_input) 
        if user_data:
            st.session_state["usuario_actual"] = user_data["nombre"]
            st.session_state["rol"] = user_data["rol"]
            st.rerun()
        else:
            st.sidebar.error("Credenciales incorrectas.")
    st.sidebar.markdown("---")
else:
    st.sidebar.success(f"👷 {st.session_state['usuario_actual']} \n\n🎯 Rol: {st.session_state['rol']}")
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state["usuario_actual"] = None
        st.session_state["rol"] = None
        st.rerun()
    st.sidebar.markdown("---")


# ============================================================
# CONTROL DE ACCESO BASADO EN ROLES (RBAC)
# ============================================================

rol_actual = st.session_state["rol"]

# Vista predeterminada (Público / No logueado)
opciones_menu = ["Chat y flujo de agentes"]

if rol_actual == "Atencion y ventas":
    opciones_menu = ["Chat y flujo de agentes", "Clientes", "Inventario"]
elif rol_actual == "Validacion tecnica":
    opciones_menu = ["Chat y flujo de agentes", "Servicios", "Reglas de inferencia"]
elif rol_actual == "Supervisor y explicador":
    # Acceso total a todas las pestañas
    opciones_menu = [
        "Dashboard",
        "Chat y flujo de agentes",
        "Clientes",
        "Inventario",
        "Servicios",
        "Reglas de inferencia",
        "Usuarios internos",
        "Historial / BD"
    ]

pagina = st.sidebar.radio("Navegación", opciones_menu)

st.sidebar.markdown("---")
st.sidebar.caption("Flujo principal:")
st.sidebar.markdown("""
1. Agente 1 interpreta  
2. Agente 2 infiere  
3. Agente 3 explica  
4. Operador valida  
""")


# ============================================================
# PÁGINA: DASHBOARD
# ============================================================

if pagina == "Dashboard":
    show_header(
        "FireGuard Expert",
        "Dashboard local para pruebas del sistema experto multiagente."
    )

    clientes = safe_call(db.obtener_clientes, [])
    productos = safe_call(db.obtener_productos, [])
    servicios = safe_call(db.obtener_servicios, [])
    reglas = safe_call(db.obtener_reglas, [])
    usuarios = safe_call(db.obtener_usuarios_internos, [])

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Clientes", len(clientes))
    col2.metric("Productos", len(productos))
    col3.metric("Servicios", len(servicios))
    col4.metric("Reglas", len(reglas))
    col5.metric("Usuarios internos", len(usuarios))

    st.markdown("### Estado del prototipo")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Agentes disponibles")
        st.markdown("- ✅ Agente 1: Atención al cliente")
        st.markdown("- ✅ Agente 2: Motor de inferencia")
        st.markdown("- ✅ Agente 3: Supervisor / Explicador")
        st.markdown("- ✅ Conexión SQLite mediante `db.py`")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Pruebas sugeridas")
        st.code("Soy Hotel Guadalajara y necesito 2 sensores de flujo.")
        st.code("Soy Taller Mecánico Ramírez, necesito mantenimiento correctivo porque la bomba tiene fuga.")
        st.code("Soy Plaza Industrial Jalisco y quiero cotizar un tablero de control.")
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# PÁGINA: CHAT Y FLUJO
# ============================================================

elif pagina == "Chat y flujo de agentes":
    show_header(
        "Chat del cliente",
        "Prueba el flujo completo: Agente 1 → Agente 2 → Agente 3."
    )

    ejemplo = st.selectbox(
        "Ejemplos rápidos",
        [
            "",
            "Hola, soy Hotel Guadalajara y necesito 2 sensores de flujo.",
            "Soy Taller Mecánico Ramírez, necesito mantenimiento correctivo porque la bomba tiene fuga.",
            "Soy Plaza Industrial Jalisco y quiero cotizar un tablero de control.",
            "Soy Universidad Tecnológica, necesito inspección sencilla del sistema contra incendio.",
            "Quiero instalar un sistema contra incendio en otro estado.",
            "Soy nuevo cliente y quiero registrarme."
        ]
    )

    mensaje_default = ejemplo if ejemplo else ""
    mensaje = st.text_area(
        "Mensaje del cliente",
        value=mensaje_default,
        height=120,
        placeholder="Escribe aquí la solicitud del cliente..."
    )

    col_a, col_b = st.columns([1, 3])

    with col_a:
        ejecutar = st.button("Analizar solicitud", type="primary", use_container_width=True)

    with col_b:
        limpiar = st.button("Limpiar resultado", use_container_width=True)

    if limpiar:
        st.session_state.pop("analisis_agente_1", None)
        st.session_state.pop("resultado_motor", None)
        st.session_state.pop("resumen_supervisor", None)
        st.rerun()

    if ejecutar:
        if not mensaje.strip():
            st.warning("Escribe un mensaje antes de analizar.")
        else:
            analisis = agente_1.analizar_mensaje(mensaje)
            resultado_motor = motor.procesar(analisis)
            resumen = supervisor.generar_resumen(resultado_motor)

            st.session_state["analisis_agente_1"] = analisis
            st.session_state["resultado_motor"] = resultado_motor
            st.session_state["resumen_supervisor"] = resumen

    analisis = st.session_state.get("analisis_agente_1")
    resultado_motor = st.session_state.get("resultado_motor")
    resumen = st.session_state.get("resumen_supervisor")

    if analisis and resultado_motor and resumen:
        tab1, tab2, tab3, tab4 = st.tabs([
            "Agente 1",
            "Agente 2",
            "Agente 3",
            "JSON técnico"
        ])

        with tab1:
            st.subheader("Agente 1 — Atención al cliente")

            c1, c2, c3 = st.columns(3)
            c1.metric("Intención", analisis.get("intencion", "N/A"))
            c2.metric(
                "Cliente",
                analisis["cliente_detectado"]["nombre"] if analisis.get("cliente_detectado") else "No detectado"
            )
            c3.metric(
                "Servicio",
                analisis["servicio_detectado"]["nombre"] if analisis.get("servicio_detectado") else "No detectado"
            )

            st.markdown("#### Productos detectados")
            productos_detectados = analisis.get("productos_detectados", [])
            if productos_detectados:
                df_productos = to_dataframe(productos_detectados)
                columnas = [col for col in ["id_producto", "nombre", "alias_detectado", "categoria", "cantidad", "stock", "precio"] if col in df_productos.columns]
                st.dataframe(df_productos[columnas], use_container_width=True)
            else:
                st.info("No se detectaron productos.")

            st.markdown("#### Datos faltantes")
            faltantes = analisis.get("datos_faltantes", [])
            if faltantes:
                for dato in faltantes:
                    st.markdown(f"<div class='warning-box'>Falta: <b>{dato}</b></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='ok-box'>No se detectaron datos faltantes.</div>", unsafe_allow_html=True)

            st.markdown("#### Respuesta sugerida")
            st.write(analisis.get("respuesta_sugerida"))

        with tab2:
            st.subheader("Agente 2 — Motor de inferencia")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tipo operación", resultado_motor.get("tipo_operacion"))
            c2.metric("Estado", resultado_motor.get("estado"))
            c3.metric("Total estimado", f"${resultado_motor.get('total_estimado', 0):,.2f} MXN")
            c4.metric("Validación", "Sí" if resultado_motor.get("requiere_validacion") else "No")

            st.markdown("#### Reglas activadas")
            reglas_activadas = resultado_motor.get("reglas_activadas", [])
            if reglas_activadas:
                df_reglas = to_dataframe(reglas_activadas)
                columnas = [col for col in ["id_regla", "nombre", "categoria", "prioridad", "agente_responsable"] if col in df_reglas.columns]
                st.dataframe(df_reglas[columnas], use_container_width=True)
            else:
                st.info("No se activaron reglas.")

            st.markdown("#### Advertencias")
            advertencias = resultado_motor.get("advertencias", [])
            if advertencias:
                for advertencia in advertencias:
                    st.markdown(f"<div class='danger-box'>{advertencia}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='ok-box'>Sin advertencias importantes.</div>", unsafe_allow_html=True)

            st.markdown("#### Recomendaciones")
            render_list(resultado_motor.get("recomendaciones", []), "Sin recomendaciones.")

        with tab3:
            st.subheader("Agente 3 — Supervisor / Explicador")

            st.markdown("#### Resumen de solicitud")
            st.write(resumen.get("resumen_solicitud"))

            c1, c2, c3 = st.columns(3)
            estimacion = resumen.get("estimacion", {})
            c1.metric("Subtotal productos", estimacion.get("subtotal_productos_formateado", "$0.00 MXN"))
            c2.metric("Costo servicio", estimacion.get("costo_servicio_base_formateado", "$0.00 MXN"))
            c3.metric("Total estimado", estimacion.get("total_estimado_formateado", "$0.00 MXN"))

            st.markdown("#### Validación")
            validacion = resumen.get("validacion", {})
            if validacion.get("requiere_validacion"):
                st.markdown("<div class='warning-box'><b>La operación requiere validación.</b></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='ok-box'><b>La operación puede pasar a preaprobación.</b></div>", unsafe_allow_html=True)

            for motivo in validacion.get("motivos", []):
                st.markdown(f"- {motivo}")

            st.markdown("#### Advertencias técnicas")
            advertencias_supervisor = resumen.get("advertencias_tecnicas", [])
            if advertencias_supervisor:
                for advertencia in advertencias_supervisor:
                    st.markdown(f"<div class='danger-box'>{advertencia}</div>", unsafe_allow_html=True)
            else:
                st.info("No hay advertencias técnicas.")

            st.markdown("#### Acciones del operador")
            acciones = resumen.get("acciones_operador", [])
            if acciones:
                cols = st.columns(max(1, min(len(acciones), 4)))
                for i, accion in enumerate(acciones):
                    with cols[i % len(cols)]:
                        st.button(accion, use_container_width=True)

            st.markdown("#### Mensaje final")
            st.write(resumen.get("mensaje_final"))

        with tab4:
            st.subheader("Salida técnica")
            st.markdown("##### Agente 1")
            compact_json(analisis)
            st.markdown("##### Agente 2")
            compact_json(resultado_motor)
            st.markdown("##### Agente 3")
            compact_json(resumen)


# ============================================================
# PÁGINA: CLIENTES
# ============================================================

elif pagina == "Clientes":
    show_header("Clientes registrados", "Consulta rápida de clientes cargados desde SQLite.")

    clientes = safe_call(db.obtener_clientes, [])
    df = to_dataframe(clientes)

    if df.empty:
        st.warning("No hay clientes cargados.")
    else:
        st.dataframe(df, use_container_width=True)


# ============================================================
# PÁGINA: INVENTARIO
# ============================================================

elif pagina == "Inventario":
    show_header("Inventario de productos", "Productos, stock, criticidad y validaciones técnicas.")

    productos = safe_call(db.obtener_productos, [])
    df = to_dataframe(productos)

    if df.empty:
        st.warning("No hay productos cargados.")
    else:
        st.dataframe(df, use_container_width=True)

        st.markdown("### Alertas rápidas")
        try:
            stock_bajo = df[(df["control_stock"] == 1) & (df["stock"] <= df["stock_minimo"])]
            precio_variable = df[df["precio_variable"] == 1]
            diseno = df[df["requiere_diseno_tecnico"] == 1]

            c1, c2, c3 = st.columns(3)
            c1.metric("Stock bajo", len(stock_bajo))
            c2.metric("Precio variable", len(precio_variable))
            c3.metric("Diseño técnico", len(diseno))
        except Exception:
            st.info("No fue posible calcular alertas rápidas con las columnas actuales.")


# ============================================================
# PÁGINA: SERVICIOS
# ============================================================

elif pagina == "Servicios":
    show_header("Servicios", "Catálogo de servicios y validaciones.")

    servicios = safe_call(db.obtener_servicios, [])

    if not servicios:
        st.warning("No hay servicios cargados.")
    else:
        for servicio in servicios:
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"### {servicio.get('nombre')}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Costo base", f"${float(servicio.get('costo_base', 0)):,.2f} MXN")
                c2.metric("Duración", f"{servicio.get('duracion_dias_base', 0)} día(s)")
                c3.metric("Validación", servicio.get("nivel_validacion"))
                c4.metric("Revisión previa", "Sí" if servicio.get("requiere_revision_previa") else "No")

                st.markdown("**Observaciones base:**")
                render_list(servicio.get("observaciones_base", []), "Sin observaciones.")
                st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# PÁGINA: REGLAS
# ============================================================

elif pagina == "Reglas de inferencia":
    show_header("Reglas de inferencia", "Base de conocimiento del sistema experto.")

    reglas = safe_call(db.obtener_reglas, [])
    df = to_dataframe(reglas)

    if df.empty:
        st.warning("No hay reglas cargadas.")
    else:
        columnas = [col for col in ["id_regla", "nombre", "categoria", "prioridad", "agente_responsable", "explicacion"] if col in df.columns]
        st.dataframe(df[columnas], use_container_width=True)

        with st.expander("Ver reglas completas en JSON"):
            compact_json(reglas)


# ============================================================
# PÁGINA: USUARIOS INTERNOS
# ============================================================

elif pagina == "Usuarios internos":
    show_header("Usuarios internos", "Roles de validación operativa, técnica y administrativa.")

    usuarios = safe_call(db.obtener_usuarios_internos, [])

    if not usuarios:
        st.warning("No hay usuarios internos cargados.")
    else:
        for usuario in usuarios:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"### {usuario.get('nombre')}")
            st.write(f"**Rol:** {usuario.get('rol')}")
            st.write(f"**Nivel de validación:** {usuario.get('nivel_validacion')}")
            st.write(f"**Requiere supervisión técnica:** {bool(usuario.get('requiere_supervision_tecnica'))}")
            st.markdown("**Puede validar:**")
            render_list(usuario.get("puede_validar", []))
            st.markdown("**Puede autorizar servicios:**")
            render_list(usuario.get("puede_autorizar_servicios", []))
            st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# PÁGINA: HISTORIAL / BD
# ============================================================

elif pagina == "Historial / BD":
    show_header("Historial y tablas operativas", "Consulta rápida de tablas generadas en SQLite.")

    tablas = [
        "pedidos",
        "detalle_pedidos",
        "solicitudes_servicio",
        "inferencias"
    ]

    for tabla in tablas:
        st.markdown(f"### Tabla: `{tabla}`")
        df = consultar_tabla(tabla)
        if df.empty:
            st.info("Sin registros o tabla vacía.")
        else:
            st.dataframe(df, use_container_width=True)