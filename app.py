import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


# ============================================================
# app.py - FireGuard Expert
# Interfaz operativa con:
# - Chat público tipo chatbot
# - Login por roles internos
# - Pruebas completas de agentes para supervisor
# - Clientes preliminares
# - Validación técnica
# - Validación operativa
# - Inventario editable
# - Historial / tablas operativas
#
# Ejecutar desde la raíz:
#   py -m streamlit run app.py
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
    st.write(
        "Revisa que `db.py`, `agente_cliente.py`, `motor_inferencia.py` "
        "y `agente_supervisor.py` estén dentro de la carpeta `src/`."
    )
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

    .muted {
        color: #6b7280;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# AGENTES
# ============================================================

agente_1 = AgenteAtencionCliente()
motor = MotorInferencia(guardar_historial=False)
supervisor = AgenteSupervisor()


# ============================================================
# UTILIDADES UI
# ============================================================

def show_header(title: str, subtitle: str = ""):
    st.markdown(f"<h1 class='fireguard-title'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p class='fireguard-subtitle'>{subtitle}</p>", unsafe_allow_html=True)


def to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(data) if data else pd.DataFrame()


def safe_call(func, default):
    try:
        return func()
    except Exception as error:
        st.warning(f"No se pudo consultar información: {error}")
        return default


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


def obtener_usuario_actual_id() -> Optional[str]:
    return st.session_state.get("id_usuario")


def obtener_rol_actual() -> Optional[str]:
    return st.session_state.get("rol")


def usuario_puede_ver(pagina: str, rol: Optional[str]) -> bool:
    if pagina == "Chat público":
        return True

    if rol == "Atencion y ventas":
        return pagina in [
            "Chat público",
            "Clientes preliminares",
            "Inventario editable",
            "Historial / BD"
        ]

    if rol == "Servicio tecnico":
        return pagina in [
            "Chat público",
            "Clientes preliminares",
            "Inventario editable",
            "Validación operativa",
            "Historial / BD"
        ]

    if rol == "Validacion tecnica":
        return pagina in [
            "Chat público",
            "Validación técnica",
            "Servicios",
            "Reglas de inferencia",
            "Historial / BD"
        ]

    if rol == "Supervisor y explicador":
        return True

    return False


# ============================================================
# LOGIN
# ============================================================

if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = None
    st.session_state["id_usuario"] = None
    st.session_state["rol"] = None
    st.session_state["nivel_validacion"] = None

st.sidebar.markdown("## 🔥 FireGuard Expert")
st.sidebar.caption("Sistema experto multiagente contra incendio")
st.sidebar.markdown("---")

st.sidebar.markdown("### 🔐 Acceso interno")

if st.session_state["usuario_actual"] is None:
    user_input = st.sidebar.text_input("ID Usuario", placeholder="Ej. U004")
    pass_input = st.sidebar.text_input("Contraseña", type="password")

    if st.sidebar.button("Iniciar sesión", type="primary", use_container_width=True):
        user_data = db.verificar_credenciales(user_input, pass_input)
        if user_data:
            st.session_state["id_usuario"] = user_data["id_usuario"]
            st.session_state["usuario_actual"] = user_data["nombre"]
            st.session_state["rol"] = user_data["rol"]
            st.session_state["nivel_validacion"] = user_data.get("nivel_validacion")
            st.rerun()
        else:
            st.sidebar.error("Credenciales incorrectas.")
else:
    st.sidebar.success(
        f"👷 {st.session_state['usuario_actual']}\n\n"
        f"🎯 Rol: {st.session_state['rol']}"
    )
    if st.sidebar.button("Cerrar sesión", use_container_width=True):
        st.session_state["id_usuario"] = None
        st.session_state["usuario_actual"] = None
        st.session_state["rol"] = None
        st.session_state["nivel_validacion"] = None
        st.rerun()

st.sidebar.markdown("---")

rol_actual = obtener_rol_actual()

todas_paginas = [
    "Chat público",
    "Dashboard",
    "Chat y flujo de agentes",
    "Clientes preliminares",
    "Validación técnica",
    "Validación operativa",
    "Inventario editable",
    "Clientes",
    "Inventario",
    "Servicios",
    "Reglas de inferencia",
    "Usuarios internos",
    "Historial / BD"
]

opciones_menu = [p for p in todas_paginas if usuario_puede_ver(p, rol_actual)]

pagina = st.sidebar.radio("Navegación", opciones_menu)

st.sidebar.markdown("---")
st.sidebar.caption("Flujo:")
st.sidebar.markdown("""
Cliente público → Agente 1  
Operación → Agente 2  
Resumen → Agente 3  
Operador / técnico / ingeniero valida
""")


# ============================================================
# PÁGINA: CHAT PÚBLICO
# ============================================================

if pagina == "Chat público":
    show_header(
        "Chat público del cliente",
        "Entrada simple tipo chatbot. El cliente no necesita iniciar sesión."
    )

    if "public_chat_id" not in st.session_state:
        try:
            st.session_state["public_chat_id"] = db.iniciar_conversacion_cliente()
        except Exception:
            st.session_state["public_chat_id"] = None

    if "public_chat_messages" not in st.session_state:
        st.session_state["public_chat_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "¡Hola! Soy el asistente de FireGuard Expert. "
                    "Puedo ayudarte con cotizaciones, inventario, mantenimiento, inspecciones, instalaciones o registro de nuevo cliente."
                )
            }
        ]

    if "public_last_analysis" not in st.session_state:
        st.session_state["public_last_analysis"] = None
        st.session_state["public_last_motor"] = None
        st.session_state["public_last_summary"] = None

    col_chat, col_acciones = st.columns([1.4, 1])

    with col_chat:
        st.markdown("### Conversación")

        for msg in st.session_state["public_chat_messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_msg = st.chat_input("Escribe tu solicitud...")

        if user_msg:
            st.session_state["public_chat_messages"].append({"role": "user", "content": user_msg})

            if st.session_state.get("public_chat_id"):
                try:
                    db.guardar_mensaje_chat(st.session_state["public_chat_id"], "cliente", user_msg)
                except Exception:
                    pass

            analisis = agente_1.analizar_mensaje(user_msg)
            resultado_motor = motor.procesar(analisis)
            resumen = supervisor.generar_resumen(resultado_motor)

            st.session_state["public_last_analysis"] = analisis
            st.session_state["public_last_motor"] = resultado_motor
            st.session_state["public_last_summary"] = resumen

            respuesta = analisis.get("respuesta_sugerida", "Recibí tu solicitud. La estamos analizando.")
            st.session_state["public_chat_messages"].append({"role": "assistant", "content": respuesta})

            if st.session_state.get("public_chat_id"):
                try:
                    db.guardar_mensaje_chat(st.session_state["public_chat_id"], "agente_1", respuesta)
                    db.actualizar_conversacion_cliente(
                        st.session_state["public_chat_id"],
                        intencion_detectada=analisis.get("intencion"),
                        id_cliente=analisis.get("cliente_detectado", {}).get("id_cliente") if analisis.get("cliente_detectado") else None
                    )
                except Exception:
                    pass

            st.rerun()

    with col_acciones:
        st.markdown("### Resultado detectado")

        analisis = st.session_state.get("public_last_analysis")
        resultado_motor = st.session_state.get("public_last_motor")
        resumen = st.session_state.get("public_last_summary")

        if not analisis:
            st.info("Cuando el cliente escriba un mensaje, aquí aparecerá el análisis.")
        else:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.write(f"**Intención:** {analisis.get('intencion')}")
            cliente = analisis.get("cliente_detectado")
            servicio = analisis.get("servicio_detectado")
            st.write(f"**Cliente:** {cliente.get('nombre') if cliente else 'No registrado / no detectado'}")
            st.write(f"**Servicio:** {servicio.get('nombre') if servicio else 'No detectado'}")
            st.write(f"**Foráneo:** {'Sí' if analisis.get('servicio_foraneo') else 'No'}")
            st.markdown("</div>", unsafe_allow_html=True)

            if analisis.get("productos_detectados"):
                st.markdown("**Productos detectados:**")
                for prod in analisis["productos_detectados"]:
                    st.write(f"- {prod.get('cantidad', 1)} x {prod.get('nombre')}")

            if analisis.get("datos_faltantes"):
                st.markdown("**Datos faltantes:**")
                for dato in analisis["datos_faltantes"]:
                    st.markdown(f"<div class='warning-box'>{dato}</div>", unsafe_allow_html=True)

            if resultado_motor:
                st.markdown("### Estimación")
                st.metric("Total estimado", f"${resultado_motor.get('total_estimado', 0):,.2f} MXN")
                st.metric("Duración base", f"{resultado_motor.get('duracion_dias_base', 0)} día(s)")

            st.markdown("---")
            st.markdown("### Guardar solicitud / cliente preliminar")

            with st.form("form_public_guardar"):
                st.caption("Completa datos mínimos si el cliente no está registrado.")

                nombre = st.text_input("Nombre / empresa", value=cliente.get("nombre") if cliente else "")
                tipo = st.selectbox("Tipo de cliente", ["Comercial", "Empresarial", "Institucional"])
                rfc = st.text_input("RFC")
                direccion = st.text_area("Dirección fiscal / ubicación")

                c1, c2 = st.columns(2)
                bomba_electrica = c1.checkbox("Bomba eléctrica", value=True)
                bomba_piloto = c1.checkbox("Bomba piloto", value=False)
                bomba_combustion = c2.checkbox("Bomba combustión", value=False)
                tablero_propio = c2.checkbox("Tablero propio", value=False)

                costo_extra = st.number_input(
                    "Costo extra por distancia / viáticos",
                    min_value=0.0,
                    value=0.0,
                    step=100.0
                )

                observaciones_logistica = st.text_area(
                    "Observaciones de logística",
                    placeholder="Ej. Servicio foráneo, traslado de material pesado, acceso a planta, etc."
                )

                guardar = st.form_submit_button("Guardar operación preliminar", type="primary")

            if guardar:
                try:
                    id_preliminar = None
                    id_cliente = cliente.get("id_cliente") if cliente else None

                    if not id_cliente:
                        id_preliminar = db.crear_cliente_preliminar(
                            nombre=nombre,
                            tipo=tipo,
                            rfc=rfc,
                            direccion=direccion,
                            bomba_electrica=bomba_electrica,
                            bomba_piloto=bomba_piloto,
                            bomba_combustion=bomba_combustion,
                            tablero_control_propio=tablero_propio,
                            observaciones="Capturado desde chat público."
                        )

                    id_solicitud = None

                    if servicio:
                        id_solicitud = db.crear_solicitud_servicio(
                            id_cliente=id_cliente,
                            id_cliente_preliminar=id_preliminar,
                            id_servicio=servicio["id_servicio"],
                            mensaje_original=analisis.get("mensaje_original"),
                            descripcion_cliente=analisis.get("mensaje_original"),
                            servicio_foraneo=bool(analisis.get("servicio_foraneo")),
                            costo_base=float(resultado_motor.get("costo_servicio_base", 0)) if resultado_motor else float(servicio.get("costo_base", 0)),
                            costo_extra_distancia=float(costo_extra),
                            duracion_dias_base=int(resultado_motor.get("duracion_dias_base", servicio.get("duracion_dias_base", 1))) if resultado_motor else int(servicio.get("duracion_dias_base", 1)),
                            nivel_validacion=servicio.get("nivel_validacion"),
                            requiere_revision_previa=bool(servicio.get("requiere_revision_previa")),
                            resumen_supervisor=resumen.get("resumen_solicitud") if resumen else None,
                            reglas_activadas=resultado_motor.get("reglas_activadas", []) if resultado_motor else [],
                            advertencias=resultado_motor.get("advertencias", []) if resultado_motor else [],
                            recomendaciones=resultado_motor.get("recomendaciones", []) if resultado_motor else [],
                            observaciones_logistica=observaciones_logistica,
                            estado="pendiente_validacion" if servicio.get("nivel_validacion") == "Tecnica" or servicio.get("requiere_revision_previa") else "pendiente_validacion_operativa"
                        )

                    if st.session_state.get("public_chat_id"):
                        db.actualizar_conversacion_cliente(
                            st.session_state["public_chat_id"],
                            estado="guardada",
                            id_cliente=id_cliente,
                            id_cliente_preliminar=id_preliminar,
                            id_solicitud=id_solicitud
                        )

                    if id_solicitud and id_preliminar:
                        st.success(f"Cliente preliminar #{id_preliminar} y solicitud #{id_solicitud} guardados.")
                    elif id_solicitud:
                        st.success(f"Solicitud #{id_solicitud} guardada.")
                    elif id_preliminar:
                        st.success(f"Cliente preliminar #{id_preliminar} guardado.")
                    else:
                        st.warning("No se guardó solicitud porque no se detectó servicio.")

                except Exception as error:
                    st.error("No se pudo guardar la operación.")
                    st.exception(error)

            if st.button("Nueva conversación", use_container_width=True):
                st.session_state.pop("public_chat_id", None)
                st.session_state.pop("public_chat_messages", None)
                st.session_state.pop("public_last_analysis", None)
                st.session_state.pop("public_last_motor", None)
                st.session_state.pop("public_last_summary", None)
                st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

elif pagina == "Dashboard":
    show_header("FireGuard Expert", "Panel principal del sistema experto multiagente.")

    clientes = safe_call(db.obtener_clientes, [])
    productos = safe_call(db.obtener_productos, [])
    servicios = safe_call(db.obtener_servicios, [])
    reglas = safe_call(db.obtener_reglas, [])
    solicitudes = safe_call(db.listar_solicitudes_servicio, [])
    preliminares = safe_call(db.listar_clientes_preliminares, [])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Clientes", len(clientes))
    col2.metric("Productos", len(productos))
    col3.metric("Servicios", len(servicios))
    col4.metric("Reglas", len(reglas))
    col5.metric("Solicitudes", len(solicitudes))

    st.markdown("### Pendientes")
    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes preliminares", len([x for x in preliminares if x.get("estado") == "pendiente_validacion"]))
    c2.metric("Solicitudes técnicas", len([x for x in solicitudes if x.get("nivel_validacion") == "Tecnica" and x.get("estado") == "pendiente_validacion"]))
    c3.metric("Solicitudes operativas", len([x for x in solicitudes if x.get("estado") == "pendiente_validacion_operativa"]))


# ============================================================
# CHAT Y FLUJO DE AGENTES - TEST INTERNO
# ============================================================

elif pagina == "Chat y flujo de agentes":
    show_header("Chat y flujo de agentes", "Vista interna para probar Agente 1 → Agente 2 → Agente 3.")

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

    mensaje = st.text_area(
        "Mensaje del cliente",
        value=ejemplo if ejemplo else "",
        height=120
    )

    col_a, col_b = st.columns([1, 3])
    ejecutar = col_a.button("Analizar solicitud", type="primary", use_container_width=True)
    limpiar = col_b.button("Limpiar resultado", use_container_width=True)

    if limpiar:
        for key in ["analisis_agente_1", "resultado_motor", "resumen_supervisor"]:
            st.session_state.pop(key, None)
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
        tab1, tab2, tab3, tab4 = st.tabs(["Agente 1", "Agente 2", "Agente 3", "JSON técnico"])

        with tab1:
            st.subheader("Agente 1 — Atención al cliente")
            c1, c2, c3 = st.columns(3)
            c1.metric("Intención", analisis.get("intencion", "N/A"))
            c2.metric("Cliente", analisis["cliente_detectado"]["nombre"] if analisis.get("cliente_detectado") else "No detectado")
            c3.metric("Servicio", analisis["servicio_detectado"]["nombre"] if analisis.get("servicio_detectado") else "No detectado")

            st.markdown("#### Productos detectados")
            df_productos = to_dataframe(analisis.get("productos_detectados", []))
            if df_productos.empty:
                st.info("No se detectaron productos.")
            else:
                columnas = [col for col in ["id_producto", "nombre", "alias_detectado", "categoria", "cantidad", "stock", "precio"] if col in df_productos.columns]
                st.dataframe(df_productos[columnas], use_container_width=True)

            st.markdown("#### Datos faltantes")
            if analisis.get("datos_faltantes"):
                render_list(analisis.get("datos_faltantes"))
            else:
                st.success("No se detectaron datos faltantes.")

            st.markdown("#### Respuesta sugerida")
            st.write(analisis.get("respuesta_sugerida"))

        with tab2:
            st.subheader("Agente 2 — Motor de inferencia")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Tipo operación", resultado_motor.get("tipo_operacion"))
            c2.metric("Estado", resultado_motor.get("estado"))
            c3.metric("Total estimado", f"${resultado_motor.get('total_estimado', 0):,.2f} MXN")
            c4.metric("Duración", f"{resultado_motor.get('duracion_dias_base', 0)} día(s)")
            c5.metric("Validación", "Sí" if resultado_motor.get("requiere_validacion") else "No")

            st.markdown("#### Reglas activadas")
            reglas_df = to_dataframe(resultado_motor.get("reglas_activadas", []))
            if reglas_df.empty:
                st.info("No se activaron reglas.")
            else:
                columnas = [col for col in ["id_regla", "nombre", "categoria", "prioridad", "agente_responsable"] if col in reglas_df.columns]
                st.dataframe(reglas_df[columnas], use_container_width=True)

            st.markdown("#### Advertencias")
            for adv in resultado_motor.get("advertencias", []):
                st.markdown(f"<div class='danger-box'>{adv}</div>", unsafe_allow_html=True)

            st.markdown("#### Recomendaciones")
            render_list(resultado_motor.get("recomendaciones", []), "Sin recomendaciones.")

            if resultado_motor.get("servicio"):
                st.markdown("#### Guardar solicitud desde prueba interna")
                costo_extra = st.number_input("Costo extra distancia", min_value=0.0, value=0.0, step=100.0)
                observaciones = st.text_area("Observaciones logística")
                if st.button("Guardar solicitud en historial", type="primary"):
                    try:
                        id_solicitud = db.crear_solicitud_desde_resultado(
                            resultado_motor,
                            resumen_supervisor=resumen,
                            id_usuario_creador=obtener_usuario_actual_id(),
                            costo_extra_distancia=costo_extra,
                            observaciones_logistica=observaciones
                        )
                        st.success(f"Solicitud guardada con ID #{id_solicitud}.")
                    except Exception as error:
                        st.error("No se pudo guardar la solicitud.")
                        st.exception(error)

        with tab3:
            st.subheader("Agente 3 — Supervisor / Explicador")
            st.write(resumen.get("resumen_solicitud"))

            estimacion = resumen.get("estimacion", {})
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Subtotal productos", estimacion.get("subtotal_productos_formateado", "$0.00 MXN"))
            c2.metric("Costo servicio", estimacion.get("costo_servicio_base_formateado", "$0.00 MXN"))
            c3.metric("Total estimado", estimacion.get("total_estimado_formateado", "$0.00 MXN"))
            c4.metric("Duración", f"{estimacion.get('duracion_dias_base', 0)} día(s)")

            st.markdown("#### Validación")
            validacion = resumen.get("validacion", {})
            if validacion.get("requiere_validacion"):
                st.warning("La operación requiere validación.")
            else:
                st.success("La operación puede pasar a preaprobación.")

            render_list(validacion.get("motivos", []), "Sin motivos.")

            st.markdown("#### Advertencias técnicas")
            render_list(resumen.get("advertencias_tecnicas", []), "Sin advertencias.")

            st.markdown("#### Acciones operador")
            render_list(resumen.get("acciones_operador", []), "Sin acciones.")

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
# CLIENTES PRELIMINARES
# ============================================================

elif pagina == "Clientes preliminares":
    show_header("Clientes preliminares", "Clientes capturados desde chat público y pendientes de validación.")

    preliminares = safe_call(db.listar_clientes_preliminares, [])
    df = to_dataframe(preliminares)

    if df.empty:
        st.info("No hay clientes preliminares.")
    else:
        st.dataframe(df, use_container_width=True)

        ids = [int(row["id_preliminar"]) for row in preliminares]
        seleccionado = st.selectbox("Selecciona cliente preliminar", ids)
        detalle = db.obtener_cliente_preliminar(seleccionado)

        if detalle:
            st.markdown("### Detalle")
            compact_json(detalle)

            c1, c2, c3 = st.columns(3)

            if c1.button("Convertir a cliente real", type="primary", use_container_width=True):
                try:
                    nuevo_id = db.convertir_cliente_preliminar_a_cliente(
                        seleccionado,
                        id_usuario_validador=obtener_usuario_actual_id()
                    )
                    st.success(f"Cliente convertido correctamente. Nuevo ID: {nuevo_id}")
                    st.rerun()
                except Exception as error:
                    st.error("No se pudo convertir el cliente.")
                    st.exception(error)

            if c2.button("Marcar aprobado sin convertir", use_container_width=True):
                db.actualizar_estado_cliente_preliminar(
                    seleccionado,
                    "aprobado",
                    id_usuario_validador=obtener_usuario_actual_id()
                )
                st.success("Cliente preliminar aprobado.")
                st.rerun()

            if c3.button("Rechazar", use_container_width=True):
                db.actualizar_estado_cliente_preliminar(
                    seleccionado,
                    "rechazado",
                    id_usuario_validador=obtener_usuario_actual_id()
                )
                st.warning("Cliente preliminar rechazado.")
                st.rerun()


# ============================================================
# VALIDACIÓN TÉCNICA
# ============================================================

elif pagina == "Validación técnica":
    show_header("Validación técnica", "Servicios correctivos e instalaciones pendientes de revisión del ingeniero.")

    solicitudes = safe_call(lambda: db.listar_solicitudes_servicio(estado="pendiente_validacion", nivel_validacion="Tecnica"), [])

    if not solicitudes:
        st.success("No hay solicitudes técnicas pendientes.")
    else:
        st.dataframe(to_dataframe(solicitudes), use_container_width=True)

        ids = [int(s["id_solicitud"]) for s in solicitudes]
        id_solicitud = st.selectbox("Selecciona solicitud", ids)
        solicitud = db.obtener_solicitud_servicio(id_solicitud)

        if solicitud:
            st.markdown("### Solicitud seleccionada")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Cliente", solicitud.get("nombre_cliente") or solicitud.get("nombre_cliente_preliminar") or "No detectado")
            c2.metric("Servicio", solicitud.get("nombre_servicio"))
            c3.metric("Costo base", f"${float(solicitud.get('costo_base', 0)):,.2f} MXN")
            c4.metric("Duración", f"{solicitud.get('duracion_dias_base')} día(s)")

            st.markdown("#### Mensaje original")
            st.write(solicitud.get("mensaje_original"))

            st.markdown("#### Advertencias")
            render_list(solicitud.get("advertencias", []), "Sin advertencias.")

            st.markdown("#### Reglas activadas")
            reglas_df = to_dataframe(solicitud.get("reglas_activadas", []))
            if not reglas_df.empty:
                columnas = [col for col in ["id_regla", "nombre", "prioridad", "explicacion"] if col in reglas_df.columns]
                st.dataframe(reglas_df[columnas], use_container_width=True)
            else:
                st.info("Sin reglas registradas.")

            with st.form("form_validacion_tecnica"):
                decision = st.selectbox("Decisión", ["aprobar", "rechazar", "mas_info", "pendiente"])
                costo_extra = st.number_input("Costo extra por distancia / viáticos", min_value=0.0, value=float(solicitud.get("costo_extra_distancia", 0)), step=100.0)
                nueva_duracion = st.number_input("Duración ajustada en días", min_value=1, value=int(solicitud.get("duracion_dias_base", 1)), step=1)
                comentarios = st.text_area("Comentarios técnicos")
                enviar = st.form_submit_button("Guardar validación", type="primary")

            if enviar:
                try:
                    id_val = db.validar_solicitud_servicio(
                        id_solicitud=id_solicitud,
                        id_usuario=obtener_usuario_actual_id(),
                        decision=decision,
                        comentarios=comentarios,
                        costo_extra_distancia=costo_extra,
                        nueva_duracion_dias=nueva_duracion
                    )
                    st.success(f"Validación guardada con ID #{id_val}.")
                    st.rerun()
                except Exception as error:
                    st.error("No se pudo guardar la validación.")
                    st.exception(error)


# ============================================================
# VALIDACIÓN OPERATIVA
# ============================================================

elif pagina == "Validación operativa":
    show_header("Validación operativa", "Preventivos e inspecciones que pueden validarse de forma más directa.")

    solicitudes = safe_call(lambda: db.listar_solicitudes_servicio(estado="pendiente_validacion_operativa"), [])

    if not solicitudes:
        st.success("No hay solicitudes operativas pendientes.")
    else:
        st.dataframe(to_dataframe(solicitudes), use_container_width=True)

        ids = [int(s["id_solicitud"]) for s in solicitudes]
        id_solicitud = st.selectbox("Selecciona solicitud", ids)
        solicitud = db.obtener_solicitud_servicio(id_solicitud)

        if solicitud:
            st.markdown("### Detalle")
            st.write(f"**Cliente:** {solicitud.get('nombre_cliente') or solicitud.get('nombre_cliente_preliminar')}")
            st.write(f"**Servicio:** {solicitud.get('nombre_servicio')}")
            st.write(f"**Costo base:** ${float(solicitud.get('costo_base', 0)):,.2f} MXN")
            st.write(f"**Duración base:** {solicitud.get('duracion_dias_base')} día(s)")

            with st.form("form_validacion_operativa"):
                decision = st.selectbox("Decisión", ["aprobar", "rechazar", "mas_info", "pendiente"])
                costo_extra = st.number_input("Costo extra por distancia / viáticos", min_value=0.0, value=float(solicitud.get("costo_extra_distancia", 0)), step=100.0)
                comentarios = st.text_area("Comentarios operativos")
                enviar = st.form_submit_button("Guardar validación", type="primary")

            if enviar:
                try:
                    id_val = db.validar_solicitud_servicio(
                        id_solicitud=id_solicitud,
                        id_usuario=obtener_usuario_actual_id(),
                        decision=decision,
                        comentarios=comentarios,
                        costo_extra_distancia=costo_extra
                    )
                    st.success(f"Validación guardada con ID #{id_val}.")
                    st.rerun()
                except Exception as error:
                    st.error("No se pudo guardar la validación.")
                    st.exception(error)


# ============================================================
# INVENTARIO EDITABLE
# ============================================================

elif pagina == "Inventario editable":
    show_header("Inventario editable", "Registrar entradas, salidas, uso en servicio o ajustes manuales.")

    productos = safe_call(db.obtener_productos, [])
    df = to_dataframe(productos)

    if df.empty:
        st.warning("No hay productos cargados.")
    else:
        st.dataframe(df, use_container_width=True)

        productos_map = {f"{p['id_producto']} - {p['nombre']}": p["id_producto"] for p in productos}

        with st.form("form_movimiento_inventario"):
            seleccion = st.selectbox("Producto", list(productos_map.keys()))
            tipo_movimiento = st.selectbox(
                "Tipo de movimiento",
                ["entrada", "reabastecimiento", "salida", "venta", "uso_en_servicio", "ajuste_manual"]
            )
            cantidad = st.number_input("Cantidad", min_value=0, value=1, step=1)
            motivo = st.text_area("Motivo")
            enviar = st.form_submit_button("Registrar movimiento", type="primary")

        if enviar:
            try:
                id_mov = db.registrar_movimiento_inventario(
                    id_producto=productos_map[seleccion],
                    tipo_movimiento=tipo_movimiento,
                    cantidad=int(cantidad),
                    motivo=motivo,
                    id_usuario=obtener_usuario_actual_id()
                )
                st.success(f"Movimiento registrado con ID #{id_mov}.")
                st.rerun()
            except Exception as error:
                st.error("No se pudo registrar el movimiento.")
                st.exception(error)

        st.markdown("### Historial de movimientos")
        movimientos = safe_call(db.listar_movimientos_inventario, [])
        if movimientos:
            st.dataframe(to_dataframe(movimientos), use_container_width=True)
        else:
            st.info("No hay movimientos registrados.")


# ============================================================
# CONSULTAS BASE
# ============================================================

elif pagina == "Clientes":
    show_header("Clientes registrados", "Clientes formales guardados en SQLite.")
    st.dataframe(to_dataframe(safe_call(db.obtener_clientes, [])), use_container_width=True)

elif pagina == "Inventario":
    show_header("Inventario de productos", "Productos cargados y estado de stock.")
    st.dataframe(to_dataframe(safe_call(db.obtener_productos, [])), use_container_width=True)

elif pagina == "Servicios":
    show_header("Servicios", "Catálogo de servicios.")

    servicios = safe_call(db.obtener_servicios, [])
    if not servicios:
        st.info("No hay servicios cargados.")
    for servicio in servicios:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"### {servicio.get('nombre')}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Costo base", f"${float(servicio.get('costo_base', 0)):,.2f} MXN")
        c2.metric("Duración", f"{servicio.get('duracion_dias_base')} día(s)")
        c3.metric("Validación", servicio.get("nivel_validacion"))
        c4.metric("Revisión previa", "Sí" if servicio.get("requiere_revision_previa") else "No")
        render_list(servicio.get("observaciones_base", []), "Sin observaciones.")
        st.markdown("</div>", unsafe_allow_html=True)

elif pagina == "Reglas de inferencia":
    show_header("Reglas de inferencia", "Base de conocimiento del sistema experto.")
    reglas = safe_call(db.obtener_reglas, [])
    df = to_dataframe(reglas)
    if df.empty:
        st.info("No hay reglas cargadas.")
    else:
        columnas = [col for col in ["id_regla", "nombre", "categoria", "prioridad", "agente_responsable", "explicacion"] if col in df.columns]
        st.dataframe(df[columnas], use_container_width=True)
        with st.expander("Ver JSON completo"):
            compact_json(reglas)

elif pagina == "Usuarios internos":
    show_header("Usuarios internos", "Roles y permisos del sistema.")
    st.dataframe(to_dataframe(safe_call(db.obtener_usuarios_internos, [])), use_container_width=True)


# ============================================================
# HISTORIAL / BD
# ============================================================

elif pagina == "Historial / BD":
    show_header("Historial y tablas operativas", "Consulta rápida de los registros generados por el sistema.")

    tabs = st.tabs([
        "Solicitudes",
        "Clientes preliminares",
        "Movimientos inventario",
        "Pedidos",
        "Inferencias",
        "Conversaciones"
    ])

    with tabs[0]:
        solicitudes = safe_call(db.listar_solicitudes_servicio, [])
        if solicitudes:
            st.dataframe(to_dataframe(solicitudes), use_container_width=True)
        else:
            st.info("Sin solicitudes registradas.")

    with tabs[1]:
        prelim = safe_call(db.listar_clientes_preliminares, [])
        if prelim:
            st.dataframe(to_dataframe(prelim), use_container_width=True)
        else:
            st.info("Sin clientes preliminares.")

    with tabs[2]:
        movimientos = safe_call(db.listar_movimientos_inventario, [])
        if movimientos:
            st.dataframe(to_dataframe(movimientos), use_container_width=True)
        else:
            st.info("Sin movimientos de inventario.")

    with tabs[3]:
        pedidos = safe_call(db.listar_pedidos, [])
        if pedidos:
            st.dataframe(to_dataframe(pedidos), use_container_width=True)
        else:
            st.info("Sin pedidos registrados.")

    with tabs[4]:
        df_inf = consultar_tabla("inferencias")
        if df_inf.empty:
            st.info("Sin inferencias guardadas.")
        else:
            st.dataframe(df_inf, use_container_width=True)

    with tabs[5]:
        conversaciones = safe_call(db.listar_conversaciones_cliente, [])
        if conversaciones:
            st.dataframe(to_dataframe(conversaciones), use_container_width=True)
        else:
            st.info("Sin conversaciones guardadas.")
