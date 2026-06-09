from typing import Any, Dict, List, Optional


class AgenteSupervisor:
    """
    Agente 3 - Supervisor / Explicador.

    Función:
    - Recibir el resultado del Agente 2 / Motor de Inferencia.
    - Generar un resumen claro para el operador.
    - Mostrar reglas activadas.
    - Mostrar advertencias técnicas.
    - Explicar decisiones.
    - Indicar si se requiere validación final.
    - Sugerir acciones disponibles para el operador.

    Este agente NO debe recalcular reglas.
    Solo organiza y explica lo que el motor de inferencia ya detectó.
    """

    def generar_resumen(self, resultado_motor: Dict[str, Any]) -> Dict[str, Any]:
        cliente = resultado_motor.get("cliente")
        productos = resultado_motor.get("productos", [])
        servicio = resultado_motor.get("servicio")
        reglas = resultado_motor.get("reglas_activadas", [])
        advertencias = resultado_motor.get("advertencias", [])
        recomendaciones = resultado_motor.get("recomendaciones", [])
        datos_faltantes = resultado_motor.get("datos_faltantes", [])

        resumen = {
            "titulo": "Resumen del Agente Supervisor",
            "tipo_operacion": resultado_motor.get("tipo_operacion", "operacion_general"),
            "estado": resultado_motor.get("estado", "pendiente_revision"),
            "resumen_solicitud": self._generar_resumen_solicitud(
                cliente=cliente,
                productos=productos,
                servicio=servicio,
                resultado_motor=resultado_motor
            ),
            "cliente": self._resumir_cliente(cliente),
            "productos": self._resumir_productos(productos),
            "servicio": self._resumir_servicio(servicio),
            "estimacion": self._generar_estimacion(resultado_motor),
            "reglas_activadas": self._resumir_reglas(reglas),
            "advertencias_tecnicas": self._ordenar_advertencias(advertencias),
            "recomendaciones_operativas": self._ordenar_recomendaciones(recomendaciones),
            "datos_faltantes": datos_faltantes,
            "validacion": self._generar_validacion(resultado_motor, reglas, advertencias, datos_faltantes),
            "acciones_operador": self._generar_acciones_operador(resultado_motor, datos_faltantes),
            "mensaje_final": self._generar_mensaje_final(resultado_motor, datos_faltantes)
        }

        return resumen

    # ============================================================
    # RESUMEN GENERAL
    # ============================================================

    def _generar_resumen_solicitud(
        self,
        cliente: Optional[Dict[str, Any]],
        productos: List[Dict[str, Any]],
        servicio: Optional[Dict[str, Any]],
        resultado_motor: Dict[str, Any]
    ) -> str:
        partes = []

        if cliente:
            partes.append(f"El cliente {cliente.get('nombre', 'sin nombre')} realizó una solicitud")
        else:
            partes.append("Se recibió una solicitud de un cliente no identificado")

        if servicio:
            partes.append(f"relacionada con el servicio de {servicio.get('nombre')}")

        if productos:
            nombres_productos = []
            for producto in productos:
                cantidad = producto.get("cantidad", 1)
                nombre = producto.get("nombre", "producto no identificado")
                nombres_productos.append(f"{cantidad} x {nombre}")

            partes.append("e incluye los productos: " + ", ".join(nombres_productos))

        if not servicio and not productos:
            partes.append("pero no se detectaron productos o servicios específicos")

        return " ".join(partes) + "."

    def _resumir_cliente(self, cliente: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not cliente:
            return {
                "detectado": False,
                "mensaje": "No se detectó un cliente registrado."
            }

        return {
            "detectado": True,
            "id_cliente": cliente.get("id_cliente"),
            "nombre": cliente.get("nombre"),
            "tipo": cliente.get("tipo"),
            "num_operaciones": cliente.get("num_operaciones"),
            "cliente_frecuente": bool(cliente.get("cliente_frecuente")),
            "fecha_ultimo_servicio": cliente.get("fecha_ultimo_servicio"),
            "rfc": cliente.get("rfc"),
            "direccion": cliente.get("direccion")
        }

    def _resumir_productos(self, productos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        resumen_productos = []

        for producto in productos:
            resumen_productos.append({
                "id_producto": producto.get("id_producto"),
                "nombre": producto.get("nombre"),
                "categoria": producto.get("categoria"),
                "subcategoria": producto.get("subcategoria"),
                "cantidad": producto.get("cantidad", 1),
                "precio": producto.get("precio", 0),
                "subtotal": producto.get("subtotal", 0),
                "stock": producto.get("stock"),
                "stock_minimo": producto.get("stock_minimo"),
                "stock_suficiente": producto.get("stock_suficiente"),
                "instalable": bool(producto.get("instalable")),
                "equipo_critico": bool(producto.get("equipo_critico")),
                "precio_variable": bool(producto.get("precio_variable")),
                "requiere_diseno_tecnico": bool(producto.get("requiere_diseno_tecnico"))
            })

        return resumen_productos

    def _resumir_servicio(self, servicio: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not servicio:
            return None

        return {
            "id_servicio": servicio.get("id_servicio"),
            "nombre": servicio.get("nombre"),
            "tipo_servicio": servicio.get("tipo_servicio"),
            "costo_base": servicio.get("costo_base"),
            "duracion_dias_base": servicio.get("duracion_dias_base"),
            "nivel_validacion": servicio.get("nivel_validacion"),
            "considera_ultimo_servicio": bool(servicio.get("considera_ultimo_servicio")),
            "requiere_revision_previa": bool(servicio.get("requiere_revision_previa"))
        }

    # ============================================================
    # ESTIMACIÓN
    # ============================================================

    def _generar_estimacion(self, resultado_motor: Dict[str, Any]) -> Dict[str, Any]:
        subtotal_productos = float(resultado_motor.get("subtotal_productos", 0))
        costo_servicio_base = float(resultado_motor.get("costo_servicio_base", 0))
        total_estimado = float(resultado_motor.get("total_estimado", 0))
        duracion_dias_base = int(resultado_motor.get("duracion_dias_base", 0))

        return {
            "subtotal_productos": subtotal_productos,
            "costo_servicio_base": costo_servicio_base,
            "total_estimado": total_estimado,
            "duracion_dias_base": duracion_dias_base,
            "subtotal_productos_formateado": self._formatear_moneda(subtotal_productos),
            "costo_servicio_base_formateado": self._formatear_moneda(costo_servicio_base),
            "total_estimado_formateado": self._formatear_moneda(total_estimado),
            "nota": "Los costos y tiempos son estimaciones base. El operador puede ajustarlos según diagnóstico, ubicación, materiales y condiciones del sitio."
        }

    # ============================================================
    # REGLAS, ADVERTENCIAS Y RECOMENDACIONES
    # ============================================================

    def _resumir_reglas(self, reglas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        reglas_resumidas = []

        for regla in reglas:
            reglas_resumidas.append({
                "id_regla": regla.get("id_regla"),
                "nombre": regla.get("nombre"),
                "categoria": regla.get("categoria"),
                "prioridad": regla.get("prioridad"),
                "agente_responsable": regla.get("agente_responsable"),
                "condicion_evaluada": regla.get("condicion_evaluada"),
                "accion_realizada": regla.get("accion_realizada"),
                "explicacion": regla.get("explicacion")
            })

        return reglas_resumidas

    def _ordenar_advertencias(self, advertencias: List[str]) -> List[str]:
        # Quita duplicados conservando orden.
        return list(dict.fromkeys(advertencias))

    def _ordenar_recomendaciones(self, recomendaciones: List[str]) -> List[str]:
        # Quita duplicados conservando orden.
        return list(dict.fromkeys(recomendaciones))

    # ============================================================
    # VALIDACIÓN
    # ============================================================

    def _generar_validacion(
        self,
        resultado_motor: Dict[str, Any],
        reglas: List[Dict[str, Any]],
        advertencias: List[str],
        datos_faltantes: List[str]
    ) -> Dict[str, Any]:
        requiere_validacion = bool(resultado_motor.get("requiere_validacion", False))

        motivos = []

        if datos_faltantes:
            motivos.append("La solicitud tiene datos faltantes.")

        if requiere_validacion:
            motivos.append("El motor de inferencia marcó la operación como pendiente de validación.")

        for regla in reglas:
            prioridad = regla.get("prioridad")
            nombre = regla.get("nombre", "")

            if prioridad == "Alta":
                motivos.append(f"Se activó una regla de prioridad alta: {nombre}.")

            if "revision" in self._normalizar(nombre) or "validacion" in self._normalizar(nombre):
                motivos.append(f"La regla '{nombre}' requiere revisión o validación.")

        if advertencias:
            motivos.append("Existen advertencias técnicas u operativas que deben revisarse.")

        if not motivos:
            motivos.append("No se detectaron bloqueos importantes. La operación puede revisarse para preaprobación.")

        return {
            "requiere_validacion": requiere_validacion or bool(datos_faltantes),
            "motivos": list(dict.fromkeys(motivos))
        }

    def _generar_acciones_operador(
        self,
        resultado_motor: Dict[str, Any],
        datos_faltantes: List[str]
    ) -> List[str]:
        acciones = []

        if datos_faltantes:
            acciones.append("Solicitar datos faltantes al cliente")
            acciones.append("Modificar datos")
            acciones.append("Cancelar operación")
            return acciones

        if resultado_motor.get("requiere_validacion"):
            acciones.append("Solicitar revisión técnica")
            acciones.append("Modificar datos")
            acciones.append("Validar operación")
            acciones.append("Cancelar operación")
        else:
            acciones.append("Validar operación")
            acciones.append("Modificar datos")
            acciones.append("Cancelar operación")

        return acciones

    def _generar_mensaje_final(
        self,
        resultado_motor: Dict[str, Any],
        datos_faltantes: List[str]
    ) -> str:
        if datos_faltantes:
            return (
                "La solicitud no puede continuar todavía porque faltan datos importantes. "
                "El operador debe solicitar la información faltante antes de enviarla nuevamente al motor de inferencia."
            )

        if resultado_motor.get("requiere_validacion"):
            return (
                "La operación requiere validación del operador o responsable técnico antes de confirmarse. "
                "Se recomienda revisar las reglas activadas, advertencias y estimaciones base."
            )

        return (
            "La operación no presenta bloqueos críticos detectados por el motor de inferencia. "
            "El operador puede validar la operación o modificar los datos si lo considera necesario."
        )

    # ============================================================
    # FORMATO PARA MOSTRAR EN CONSOLA O STREAMLIT
    # ============================================================

    def generar_texto_para_operador(self, resumen: Dict[str, Any]) -> str:
        """
        Genera una versión en texto del resumen.
        Esto sirve para pruebas en consola o para mostrarlo rápido en Streamlit.
        """
        lineas = []

        lineas.append("===== AGENTE 3: SUPERVISOR / EXPLICADOR =====")
        lineas.append("")
        lineas.append("RESUMEN DE SOLICITUD:")
        lineas.append(resumen["resumen_solicitud"])
        lineas.append("")

        cliente = resumen.get("cliente", {})
        if cliente.get("detectado"):
            lineas.append("CLIENTE:")
            lineas.append(f"- ID: {cliente.get('id_cliente')}")
            lineas.append(f"- Nombre: {cliente.get('nombre')}")
            lineas.append(f"- Tipo: {cliente.get('tipo')}")
            lineas.append(f"- Cliente frecuente: {cliente.get('cliente_frecuente')}")
            lineas.append("")
        else:
            lineas.append("CLIENTE:")
            lineas.append("- No se detectó cliente registrado.")
            lineas.append("")

        productos = resumen.get("productos", [])
        if productos:
            lineas.append("PRODUCTOS:")
            for producto in productos:
                lineas.append(
                    f"- {producto.get('cantidad')} x {producto.get('nombre')} | "
                    f"Subtotal: {self._formatear_moneda(producto.get('subtotal', 0))}"
                )
            lineas.append("")

        servicio = resumen.get("servicio")
        if servicio:
            lineas.append("SERVICIO:")
            lineas.append(f"- Nombre: {servicio.get('nombre')}")
            lineas.append(f"- Nivel de validación: {servicio.get('nivel_validacion')}")
            lineas.append(f"- Requiere revisión previa: {servicio.get('requiere_revision_previa')}")
            lineas.append("")

        estimacion = resumen.get("estimacion", {})
        lineas.append("ESTIMACIÓN:")
        lineas.append(f"- Subtotal productos: {estimacion.get('subtotal_productos_formateado')}")
        lineas.append(f"- Costo servicio base: {estimacion.get('costo_servicio_base_formateado')}")
        lineas.append(f"- Total estimado: {estimacion.get('total_estimado_formateado')}")
        lineas.append(f"- Duración base: {estimacion.get('duracion_dias_base')} día(s)")
        lineas.append("")

        reglas = resumen.get("reglas_activadas", [])
        if reglas:
            lineas.append("REGLAS ACTIVADAS:")
            for regla in reglas:
                lineas.append(f"- {regla.get('id_regla')} | {regla.get('nombre')}")
            lineas.append("")

        advertencias = resumen.get("advertencias_tecnicas", [])
        if advertencias:
            lineas.append("ADVERTENCIAS TÉCNICAS:")
            for advertencia in advertencias:
                lineas.append(f"- {advertencia}")
            lineas.append("")

        recomendaciones = resumen.get("recomendaciones_operativas", [])
        if recomendaciones:
            lineas.append("RECOMENDACIONES OPERATIVAS:")
            for recomendacion in recomendaciones:
                lineas.append(f"- {recomendacion}")
            lineas.append("")

        validacion = resumen.get("validacion", {})
        lineas.append("VALIDACIÓN:")
        lineas.append(f"- Requiere validación: {validacion.get('requiere_validacion')}")
        for motivo in validacion.get("motivos", []):
            lineas.append(f"- {motivo}")
        lineas.append("")

        lineas.append("ACCIONES DISPONIBLES:")
        for accion in resumen.get("acciones_operador", []):
            lineas.append(f"- {accion}")

        lineas.append("")
        lineas.append("MENSAJE FINAL:")
        lineas.append(resumen.get("mensaje_final", ""))

        return "\n".join(lineas)

    # ============================================================
    # UTILIDADES
    # ============================================================

    def _formatear_moneda(self, cantidad: float) -> str:
        try:
            return f"${float(cantidad):,.2f} MXN"
        except (ValueError, TypeError):
            return "$0.00 MXN"

    def _normalizar(self, texto: str) -> str:
        return str(texto).lower().strip()


# ============================================================
# PRUEBA RÁPIDA
# Ejecuta:
#   python src/agente_supervisor.py
# ============================================================

if __name__ == "__main__":
    from agente_cliente import AgenteAtencionCliente
    from motor_inferencia import MotorInferencia

    agente_1 = AgenteAtencionCliente()
    motor = MotorInferencia(guardar_historial=False)
    supervisor = AgenteSupervisor()

    mensaje = input("Mensaje del cliente: ")

    analisis = agente_1.analizar_mensaje(mensaje)
    resultado_motor = motor.procesar(analisis)
    resumen = supervisor.generar_resumen(resultado_motor)

    print()
    print(supervisor.generar_texto_para_operador(resumen))