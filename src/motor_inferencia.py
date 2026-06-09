from datetime import datetime
from typing import Any, Dict, List, Optional

import db


class MotorInferencia:
    """
    Agente 2 - Motor de Inferencia / Generador de Pedido o Servicio.

    Recibe la salida del Agente 1 y aplica reglas de inferencia usando:
    - clientes
    - productos
    - servicios
    - reglas_inferencia
    - datos detectados en el mensaje

    Este agente NO debe redactar el resumen final para el operador.
    Esa parte le corresponde al Agente 3.
    """

    def __init__(self, guardar_historial: bool = False):
        """
        guardar_historial:
            False → solo procesa en memoria.
            True  → guarda inferencias activadas en SQLite.
        """
        self.guardar_historial = guardar_historial
        self.reglas = self._cargar_reglas_por_id()

    # ============================================================
    # MÉTODO PRINCIPAL
    # ============================================================

    def procesar(self, analisis_agente_1: Dict[str, Any]) -> Dict[str, Any]:
        mensaje_original = analisis_agente_1.get("mensaje_original", "")
        intencion = analisis_agente_1.get("intencion", "general")
        cliente = analisis_agente_1.get("cliente_detectado")
        productos = analisis_agente_1.get("productos_detectados", [])
        servicio = analisis_agente_1.get("servicio_detectado")
        servicio_foraneo = analisis_agente_1.get("servicio_foraneo", False)
        datos_faltantes = analisis_agente_1.get("datos_faltantes", [])

        resultado = {
            "mensaje_original": mensaje_original,
            "intencion": intencion,
            "tipo_operacion": self._determinar_tipo_operacion(intencion, productos, servicio),
            "cliente": cliente,
            "productos": [],
            "servicio": servicio,
            "subtotal_productos": 0,
            "costo_servicio_base": 0,
            "total_estimado": 0,
            "duracion_dias_base": 0,
            "reglas_activadas": [],
            "advertencias": [],
            "recomendaciones": [],
            "datos_faltantes": datos_faltantes,
            "servicio_foraneo": servicio_foraneo,
            "requiere_validacion": False,
            "estado": "pendiente_revision"
        }

        if datos_faltantes:
            self._activar_regla(
                resultado=resultado,
                id_regla="R031",
                condicion_evaluada="datos_obligatorios_faltantes = true",
                accion_realizada="Solicitar información faltante antes de generar operación"
            )
            resultado["requiere_validacion"] = True
            resultado["estado"] = "incompleto"
            return resultado

        if cliente:
            self._evaluar_cliente(resultado, cliente, servicio, productos)

        if productos:
            self._evaluar_productos(resultado, productos)

        if servicio:
            self._evaluar_servicio(resultado, servicio)

        if servicio_foraneo:
            self._activar_regla(
                resultado=resultado,
                id_regla="R029",
                condicion_evaluada="solicitud.servicio_foraneo = true",
                accion_realizada="Advertir sobre viáticos, traslado y movilidad"
            )
            resultado["advertencias"].append(
                "El servicio parece ser foráneo. Puede requerir viáticos, traslado de personal y movilidad de material."
            )
            resultado["requiere_validacion"] = True

        self._calcular_totales(resultado)

        if resultado["requiere_validacion"]:
            resultado["estado"] = "pendiente_validacion"
        else:
            resultado["estado"] = "preaprobado"

        return resultado

    # ============================================================
    # CARGA DE REGLAS
    # ============================================================

    def _cargar_reglas_por_id(self) -> Dict[str, Dict[str, Any]]:
        reglas = db.obtener_reglas()
        return {regla["id_regla"]: regla for regla in reglas}

    def _activar_regla(
        self,
        resultado: Dict[str, Any],
        id_regla: str,
        condicion_evaluada: str,
        accion_realizada: str
    ) -> None:
        regla = self.reglas.get(id_regla, {
            "id_regla": id_regla,
            "nombre": "Regla no encontrada",
            "categoria": "Desconocida",
            "prioridad": "Media",
            "agente_responsable": "Agente 2 - Motor de Inferencia",
            "explicacion": "La regla fue activada, pero no se encontró su descripción en la base de conocimiento."
        })

        regla_activada = {
            "id_regla": regla.get("id_regla"),
            "nombre": regla.get("nombre"),
            "categoria": regla.get("categoria"),
            "prioridad": regla.get("prioridad"),
            "agente_responsable": regla.get("agente_responsable"),
            "condicion_evaluada": condicion_evaluada,
            "accion_realizada": accion_realizada,
            "explicacion": regla.get("explicacion")
        }

        resultado["reglas_activadas"].append(regla_activada)

        if self.guardar_historial:
            try:
                db.guardar_inferencia(
                    tipo_operacion=resultado.get("tipo_operacion", "operacion"),
                    id_regla=id_regla,
                    mensaje_original=resultado.get("mensaje_original"),
                    intencion_detectada=resultado.get("intencion"),
                    condicion_evaluada=condicion_evaluada,
                    accion_realizada=accion_realizada,
                    resultado="Regla activada",
                    explicacion=regla.get("explicacion")
                )
            except Exception as error:
                resultado["advertencias"].append(
                    f"No se pudo guardar la inferencia en historial: {error}"
                )

    # ============================================================
    # CLIENTE
    # ============================================================

    def _evaluar_cliente(
        self,
        resultado: Dict[str, Any],
        cliente: Dict[str, Any],
        servicio: Optional[Dict[str, Any]],
        productos: List[Dict[str, Any]]
    ) -> None:
        num_operaciones = int(cliente.get("num_operaciones", 0))

        if num_operaciones >= 10:
            self._activar_regla(
                resultado,
                "R001",
                f"cliente.num_operaciones = {num_operaciones} >= 10",
                "Clasificar cliente como frecuente"
            )

            self._activar_regla(
                resultado,
                "R035",
                "cliente.cliente_frecuente = true",
                "Sugerir beneficio comercial sujeto a validación del operador"
            )

            resultado["recomendaciones"].append(
                "El cliente es frecuente. Se puede considerar prioridad o beneficio comercial sujeto a validación."
            )
        else:
            self._activar_regla(
                resultado,
                "R002",
                f"cliente.num_operaciones = {num_operaciones} < 10",
                "Clasificar cliente como no frecuente"
            )

        if servicio and servicio.get("considera_ultimo_servicio"):
            meses = self._meses_desde_fecha(cliente.get("fecha_ultimo_servicio"))

            if meses is not None and meses > 6:
                self._activar_regla(
                    resultado,
                    "R003",
                    f"meses_desde(cliente.fecha_ultimo_servicio) = {meses} > 6",
                    "Recomendar mantenimiento preventivo"
                )
                resultado["recomendaciones"].append(
                    f"Han pasado aproximadamente {meses} meses desde el último servicio. Se recomienda mantenimiento preventivo."
                )

        facturacion = self._cliente_tiene_facturacion(cliente)

        if facturacion:
            self._activar_regla(
                resultado,
                "R032",
                "cliente.facturacion.rfc IS NOT NULL AND cliente.facturacion.direccion IS NOT NULL",
                "Usar datos de facturación registrados"
            )

        equipo = cliente.get("equipo_instalado", {})

        if not bool(equipo.get("tablero_control_propio", True)):
            self._activar_regla(
                resultado,
                "R004",
                "cliente.equipo_instalado.tablero_control_propio = false",
                "Agregar advertencia de tablero externo al resumen"
            )
            resultado["advertencias"].append(
                "El cliente tiene tablero de control externo. El operador debe decidir si se incluye en el alcance."
            )
            resultado["requiere_validacion"] = True

        tipo_cliente = cliente.get("tipo")

        if tipo_cliente == "Comercial":
            self._activar_regla(
                resultado,
                "R005",
                "cliente.tipo = 'Comercial'",
                "Recomendar protección de mercancía y aislamiento del área"
            )
            resultado["recomendaciones"].append(
                "Cliente comercial: considerar lonas, protección de mercancía y aislamiento del área."
            )

        elif tipo_cliente == "Empresarial":
            self._activar_regla(
                resultado,
                "R006",
                "cliente.tipo = 'Empresarial'",
                "Recomendar coordinación con área técnica interna"
            )
            resultado["recomendaciones"].append(
                "Cliente empresarial: coordinar acceso con área técnica o mantenimiento interno."
            )

        elif tipo_cliente == "Institucional":
            self._activar_regla(
                resultado,
                "R007",
                "cliente.tipo = 'Institucional'",
                "Recomendar coordinación con responsables del edificio"
            )
            resultado["recomendaciones"].append(
                "Cliente institucional: coordinar horarios de baja afluencia y responsables del edificio."
            )

        if bool(equipo.get("bomba_combustion", False)):
            self._activar_regla(
                resultado,
                "R008",
                "cliente.equipo_instalado.bomba_combustion = true",
                "Recomendar revisión del motor de combustión"
            )
            resultado["recomendaciones"].append(
                "Equipo con combustión: revisar aceite, filtros, arranque y sistema de combustible."
            )

        if bool(equipo.get("bomba_piloto", False)):
            self._activar_regla(
                resultado,
                "R009",
                "cliente.equipo_instalado.bomba_piloto = true",
                "Recomendar revisión de bomba piloto"
            )
            resultado["recomendaciones"].append(
                "Equipo con bomba piloto: revisar presión constante, arranque y paro automático."
            )

        if bool(equipo.get("bomba_electrica", False)):
            self._activar_regla(
                resultado,
                "R010",
                "cliente.equipo_instalado.bomba_electrica = true",
                "Recomendar revisión del motor eléctrico"
            )
            resultado["recomendaciones"].append(
                "Equipo eléctrico: revisar alimentación, conexiones, protecciones y arranque."
            )

        if productos:
            for producto in productos:
                if producto.get("equipo_critico") and self._cliente_vencido(cliente):
                    self._activar_regla(
                        resultado,
                        "R034",
                        "producto.requiere_mantenimiento = true AND meses_desde(cliente.fecha_ultimo_servicio) > 6",
                        "Recomendar revisión o mantenimiento preventivo relacionado con el producto"
                    )
                    resultado["recomendaciones"].append(
                        f"El producto {producto.get('nombre')} requiere mantenimiento y el cliente tiene servicio vencido."
                    )
                    break

    # ============================================================
    # PRODUCTOS
    # ============================================================

    def _evaluar_productos(
        self,
        resultado: Dict[str, Any],
        productos: List[Dict[str, Any]]
    ) -> None:
        for producto in productos:
            cantidad = int(producto.get("cantidad", 1))
            precio = float(producto.get("precio", 0))
            stock = int(producto.get("stock", 0))
            stock_minimo = int(producto.get("stock_minimo", 0))
            control_stock = bool(producto.get("control_stock", True))

            subtotal = precio * cantidad

            producto_resultado = dict(producto)
            producto_resultado["subtotal"] = subtotal
            producto_resultado["stock_suficiente"] = None

            if control_stock:
                if stock >= cantidad:
                    self._activar_regla(
                        resultado,
                        "R011",
                        f"producto.stock = {stock} >= cantidad_solicitada = {cantidad}",
                        "Permitir generación de pedido y calcular subtotal"
                    )
                    producto_resultado["stock_suficiente"] = True
                else:
                    self._activar_regla(
                        resultado,
                        "R012",
                        f"producto.stock = {stock} < cantidad_solicitada = {cantidad}",
                        "Bloquear confirmación directa y sugerir reabastecimiento"
                    )
                    resultado["advertencias"].append(
                        f"Stock insuficiente para {producto.get('nombre')}: solicitado {cantidad}, disponible {stock}."
                    )
                    resultado["requiere_validacion"] = True
                    producto_resultado["stock_suficiente"] = False

                if stock <= stock_minimo:
                    self._activar_regla(
                        resultado,
                        "R013",
                        f"producto.stock = {stock} <= producto.stock_minimo = {stock_minimo}",
                        "Generar alerta de reabastecimiento"
                    )
                    resultado["advertencias"].append(
                        f"{producto.get('nombre')} está en stock mínimo o por debajo del mínimo."
                    )
            else:
                self._activar_regla(
                    resultado,
                    "R018",
                    "producto.control_stock = false",
                    "No descontar inventario automáticamente y enviar a validación"
                )
                resultado["advertencias"].append(
                    f"{producto.get('nombre')} no se maneja como inventario estándar."
                )
                resultado["requiere_validacion"] = True

            if bool(producto.get("instalable", False)):
                self._activar_regla(
                    resultado,
                    "R014",
                    "producto.instalable = true AND intencion IN ['compra', 'cotizacion']",
                    "Sugerir servicio de instalación relacionado"
                )
                resultado["recomendaciones"].append(
                    f"{producto.get('nombre')} es instalable. Se puede sugerir servicio de instalación."
                )

            if bool(producto.get("equipo_critico", False)):
                self._activar_regla(
                    resultado,
                    "R015",
                    "producto.equipo_critico = true",
                    "Asignar prioridad alta a la solicitud"
                )
                resultado["recomendaciones"].append(
                    f"{producto.get('nombre')} es equipo crítico para el sistema contra incendio."
                )

            if bool(producto.get("precio_variable", False)):
                self._activar_regla(
                    resultado,
                    "R016",
                    "producto.precio_variable = true",
                    "Advertir que el precio base es referencial"
                )
                resultado["advertencias"].append(
                    f"{producto.get('nombre')} tiene precio variable. Requiere validación del operador."
                )
                resultado["requiere_validacion"] = True

            if bool(producto.get("requiere_diseno_tecnico", False)):
                self._activar_regla(
                    resultado,
                    "R017",
                    "producto.requiere_diseno_tecnico = true",
                    "Solicitar revisión técnica previa"
                )
                resultado["advertencias"].append(
                    f"{producto.get('nombre')} requiere diseño técnico antes de cerrar venta o instalación."
                )
                resultado["requiere_validacion"] = True

            self._evaluar_recomendaciones_por_categoria(resultado, producto)

            resultado["productos"].append(producto_resultado)

    def _evaluar_recomendaciones_por_categoria(
        self,
        resultado: Dict[str, Any],
        producto: Dict[str, Any]
    ) -> None:
        categoria = producto.get("categoria")
        subcategoria = producto.get("subcategoria")
        nombre = producto.get("nombre")

        if categoria == "Motor" and subcategoria == "Combustion":
            self._activar_regla(
                resultado,
                "R019",
                "producto.categoria = 'Motor' AND producto.subcategoria = 'Combustion'",
                "Recomendar revisión de aceite, filtros, combustible, arranque y estado mecánico"
            )
            resultado["recomendaciones"].append(
                f"{nombre}: considerar revisión de aceite, filtros, combustible y arranque."
            )

        if categoria == "Motor" and subcategoria == "Electrico":
            self._activar_regla(
                resultado,
                "R020",
                "producto.categoria = 'Motor' AND producto.subcategoria = 'Electrico'",
                "Recomendar revisión eléctrica del motor"
            )
            resultado["recomendaciones"].append(
                f"{nombre}: revisar alimentación, conexiones, protecciones y arranque."
            )

        if categoria == "Bomba":
            self._activar_regla(
                resultado,
                "R021",
                "producto.categoria = 'Bomba'",
                "Recomendar revisión hidráulica de bomba"
            )
            resultado["recomendaciones"].append(
                f"{nombre}: revisar presión, acoplamiento, goteos, fugas, sellos mecánicos, succión y descarga."
            )

        if categoria == "Sensor":
            self._activar_regla(
                resultado,
                "R022",
                "producto.categoria = 'Sensor'",
                "Recomendar prueba funcional, señal y comunicación con tablero"
            )
            resultado["recomendaciones"].append(
                f"{nombre}: realizar prueba funcional y verificar señal hacia tablero."
            )

        if categoria == "Valvula":
            self._activar_regla(
                resultado,
                "R023",
                "producto.categoria = 'Valvula'",
                "Recomendar revisión de apertura, cierre, fugas, retorno y presión"
            )
            resultado["recomendaciones"].append(
                f"{nombre}: revisar apertura, cierre, fugas, retorno y presión."
            )

    # ============================================================
    # SERVICIOS
    # ============================================================

    def _evaluar_servicio(
        self,
        resultado: Dict[str, Any],
        servicio: Dict[str, Any]
    ) -> None:
        resultado["costo_servicio_base"] = float(servicio.get("costo_base", 0))
        resultado["duracion_dias_base"] = int(servicio.get("duracion_dias_base", 0))

        if servicio.get("nivel_validacion") == "Tecnica":
            self._activar_regla(
                resultado,
                "R024",
                "servicio.nivel_validacion = 'Tecnica'",
                "Advertir que el servicio requiere validación técnica"
            )
            resultado["advertencias"].append(
                f"El servicio {servicio.get('nombre')} requiere validación técnica."
            )
            resultado["requiere_validacion"] = True

        if bool(servicio.get("requiere_revision_previa", False)):
            self._activar_regla(
                resultado,
                "R025",
                "servicio.requiere_revision_previa = true",
                "Bloquear confirmación final automática hasta revisión previa"
            )
            resultado["advertencias"].append(
                f"El servicio {servicio.get('nombre')} requiere revisión previa antes de confirmar alcance, costo y duración."
            )
            resultado["requiere_validacion"] = True

        tipo_servicio = servicio.get("tipo_servicio")

        if tipo_servicio == "Correctivo":
            self._activar_regla(
                resultado,
                "R026",
                "servicio.tipo_servicio = 'Correctivo'",
                "Solicitar descripción de la falla y diagnóstico antes de confirmar reparación"
            )
            resultado["advertencias"].append(
                "El mantenimiento correctivo requiere diagnóstico previo antes de confirmar reparación."
            )
            resultado["requiere_validacion"] = True

        if tipo_servicio == "Instalacion":
            self._activar_regla(
                resultado,
                "R027",
                "servicio.tipo_servicio = 'Instalacion'",
                "Solicitar información del sitio y enviar a validación técnica"
            )
            resultado["advertencias"].append(
                "La instalación requiere información del sitio, planos, condiciones técnicas y validación de ingeniería."
            )
            resultado["requiere_validacion"] = True

        if tipo_servicio == "Inspeccion":
            self._activar_regla(
                resultado,
                "R028",
                "servicio.tipo_servicio = 'Inspeccion'",
                "La inspección puede derivar en mantenimiento correctivo si se detecta falla crítica"
            )
            resultado["recomendaciones"].append(
                "Si durante la inspección se detecta una falla crítica, se debe sugerir mantenimiento correctivo."
            )

        self._activar_regla(
            resultado,
            "R030",
            "solicitud.tipo = 'servicio'",
            "Mostrar costo_base y duracion_dias_base como estimaciones"
        )
        resultado["advertencias"].append(
            "El costo y la duración son estimaciones base; pueden cambiar según diagnóstico, ubicación y condiciones del sitio."
        )

    # ============================================================
    # CÁLCULOS Y UTILIDADES
    # ============================================================

    def _calcular_totales(self, resultado: Dict[str, Any]) -> None:
        subtotal_productos = sum(
            float(producto.get("subtotal", 0)) for producto in resultado["productos"]
        )

        costo_servicio = float(resultado.get("costo_servicio_base", 0))

        resultado["subtotal_productos"] = subtotal_productos
        resultado["total_estimado"] = subtotal_productos + costo_servicio

    def _determinar_tipo_operacion(
        self,
        intencion: str,
        productos: List[Dict[str, Any]],
        servicio: Optional[Dict[str, Any]]
    ) -> str:
        if intencion == "registro_cliente":
            return "registro_cliente"

        if productos and servicio:
            return "operacion_mixta"

        if productos:
            return "pedido_producto"

        if servicio:
            return "solicitud_servicio"

        if intencion == "consulta_inventario":
            return "consulta_inventario"

        return "operacion_general"

    def _cliente_tiene_facturacion(self, cliente: Dict[str, Any]) -> bool:
        rfc = cliente.get("rfc") or cliente.get("facturacion", {}).get("rfc")
        direccion = cliente.get("direccion") or cliente.get("facturacion", {}).get("direccion")
        return bool(rfc and direccion)

    def _cliente_vencido(self, cliente: Dict[str, Any]) -> bool:
        meses = self._meses_desde_fecha(cliente.get("fecha_ultimo_servicio"))
        return meses is not None and meses > 6

    def _meses_desde_fecha(self, fecha_texto: Optional[str]) -> Optional[int]:
        if not fecha_texto:
            return None

        try:
            fecha = datetime.strptime(fecha_texto, "%Y-%m-%d")
            hoy = datetime.now()
            return (hoy.year - fecha.year) * 12 + (hoy.month - fecha.month)
        except ValueError:
            return None


# ============================================================
# PRUEBA RÁPIDA
# Ejecuta:
#   python src/motor_inferencia.py
# ============================================================

if __name__ == "__main__":
    from agente_cliente import AgenteAtencionCliente

    agente_1 = AgenteAtencionCliente()
    motor = MotorInferencia(guardar_historial=False)

    mensaje = input("Mensaje del cliente: ")

    analisis = agente_1.analizar_mensaje(mensaje)
    resultado = motor.procesar(analisis)

    print("\n===== RESULTADO DEL MOTOR DE INFERENCIA =====")
    print("Tipo de operación:", resultado["tipo_operacion"])
    print("Estado:", resultado["estado"])
    print("Total estimado:", resultado["total_estimado"])
    print("Requiere validación:", resultado["requiere_validacion"])

    print("\nReglas activadas:")
    for regla in resultado["reglas_activadas"]:
        print(f"- {regla['id_regla']} | {regla['nombre']}")

    print("\nAdvertencias:")
    for advertencia in resultado["advertencias"]:
        print(f"- {advertencia}")

    print("\nRecomendaciones:")
    for recomendacion in resultado["recomendaciones"]:
        print(f"- {recomendacion}")