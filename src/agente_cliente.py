
import re
from typing import Any, Dict, List, Optional

import db


# ============================================================
# agente_cliente.py
# Agente 1 - Enfoque Chatbot Conversacional
# ============================================================

class AgenteAtencionCliente:
    def analizar_mensaje(self, mensaje: str) -> Dict[str, Any]:
        mensaje = mensaje.strip()

        if not mensaje:
            return {
                "mensaje_original": mensaje,
                "intencion": "sin_mensaje",
                "cliente_detectado": None,
                "productos_detectados": [],
                "servicio_detectado": None,
                "servicio_foraneo": False,
                "datos_faltantes": ["mensaje"],
                "respuesta_sugerida": "¡Hola! Soy tu asistente de FireGuard. ¿En qué puedo ayudarte hoy con tu sistema contra incendios?"
            }

        # 1. Buscar entidades primero para no depender de palabras clave ambiguas
        cliente = db.buscar_cliente_en_texto(mensaje)
        productos = self._detectar_productos(mensaje)
        servicio = db.buscar_servicio_en_texto(mensaje)
        servicio_foraneo = self._detectar_servicio_foraneo(mensaje)
        
        # 2. Determinar intención de forma inteligente
        intencion = self._determinar_intencion_inteligente(mensaje, productos, servicio)
        
        # 3. Detectar qué información falta según el contexto real
        datos_faltantes = self._detectar_datos_faltantes(
            intencion=intencion,
            cliente=cliente,
            productos=productos,
            servicio=servicio,
            mensaje=mensaje
        )

        # 4. Respuesta en formato Chatbot Conversacional
        respuesta_sugerida = self._generar_respuesta_chatbot(
            intencion=intencion,
            cliente=cliente,
            productos=productos,
            servicio=servicio,
            datos_faltantes=datos_faltantes
        )

        return {
            "mensaje_original": mensaje,
            "intencion": intencion,
            "cliente_detectado": cliente,
            "productos_detectados": productos,
            "servicio_detectado": servicio,
            "servicio_foraneo": servicio_foraneo,
            "datos_faltantes": datos_faltantes,
            "respuesta_sugerida": respuesta_sugerida
        }

    def _determinar_intencion_inteligente(self, mensaje: str, productos: list, servicio: Optional[dict]) -> str:
        texto = db.texto_normalizado(mensaje)
        
        palabras_registro = ["registrarme", "registrar cliente", "dar de alta", "alta de cliente", "nuevo cliente", "agregar cliente", "no estoy registrado"]
        if any(palabra in texto for palabra in palabras_registro):
            return "registro_cliente"
            
        palabras_inventario = ["stock", "inventario", "disponible", "tienes", "hay existencia", "existencia"]
        if any(palabra in texto for palabra in palabras_inventario) and not servicio:
            return "consulta_inventario"

        # Resolución del BUG: Clasificación basada en lo que realmente contiene el mensaje
        if productos and servicio:
            return "mixta"
        if servicio:
            return "servicio"
        if productos:
            return "compra_cotizacion"
            
        return "general"

    def _detectar_productos(self, mensaje: str) -> List[Dict[str, Any]]:
        productos_base = db.buscar_productos_en_texto(mensaje)
        productos_detectados = []

        for producto in productos_base:
            cantidad = self._detectar_cantidad_cerca_de_alias(mensaje=mensaje, alias=producto["alias"])
            productos_detectados.append({
                "id_producto": producto["id_producto"],
                "nombre": producto["nombre"],
                "alias_detectado": producto["alias"],
                "categoria": producto["categoria"],
                "subcategoria": producto["subcategoria"],
                "cantidad": cantidad,
                "precio": producto["precio"],
                "stock": producto["stock"],
                "stock_minimo": producto["stock_minimo"],
                "control_stock": bool(producto["control_stock"]),
                "instalable": bool(producto["instalable"]),
                "equipo_critico": bool(producto["equipo_critico"]),
                "precio_variable": bool(producto["precio_variable"]),
                "requiere_diseno_tecnico": bool(producto["requiere_diseno_tecnico"])
            })
        return productos_detectados

    def _detectar_cantidad_cerca_de_alias(self, mensaje: str, alias: str) -> int:
        texto = db.texto_normalizado(mensaje)
        alias_norm = db.texto_normalizado(alias)
        posicion = texto.find(alias_norm)
        if posicion == -1: return 1

        texto_previo = texto[max(0, posicion - 40):posicion]
        for patron in [r"(\d+)\s*(piezas|pieza|pz|unidades|unidad|u)?\s*(de\s+)?$", r"(\d+)\s*$"]:
            coincidencia = re.search(patron, texto_previo)
            if coincidencia: return max(1, int(coincidencia.group(1)))

        texto_posterior = texto[posicion + len(alias_norm): posicion + len(alias_norm) + 40]
        for patron in [r"^\s*(?:,|:|—|\bson\b)?\s*(\d+)\s*(piezas|pieza|pz|unidades|unidad|u)?", r"^\s*(\d+)"]:
            coincidencia = re.search(patron, texto_posterior)
            if coincidencia: return max(1, int(coincidencia.group(1)))
        return 1

    def _detectar_servicio_foraneo(self, mensaje: str) -> bool:
        texto = db.texto_normalizado(mensaje)
        return any(p in texto for p in ["foraneo", "otro estado", "fuera de jalisco", "viajar", "traslado", "viaticos"])

    def _detectar_datos_faltantes(self, intencion: str, cliente: Optional[Dict[str, Any]], productos: List[Dict[str, Any]], servicio: Optional[Dict[str, Any]], mensaje: str) -> List[str]:
        faltantes = []
        texto = db.texto_normalizado(mensaje)

        # Si el usuario explícitamente se quiere registrar, omitimos la validación de cliente existente
        if intencion != "registro_cliente" and intencion in ["compra_cotizacion", "servicio", "mixta", "consulta_inventario"]:
            if cliente is None:
                faltantes.append("identificación_cliente")

        if intencion in ["compra_cotizacion", "mixta"] and not productos:
            faltantes.append("producto_especifico")

        if intencion in ["servicio", "mixta"]:
            if servicio is None:
                faltantes.append("tipo_de_servicio")
            if servicio and servicio.get("tipo_servicio") == "Correctivo":
                if not any(p in texto for p in ["falla", "no funciona", "fuga", "goteo", "problema", "daño"]):
                    faltantes.append("descripción_de_la_falla")
            if servicio and servicio.get("tipo_servicio") == "Instalacion":
                if not any(p in texto for p in ["plano", "sitio", "ubicacion", "bodega", "area"]):
                    faltantes.append("información_del_sitio_o_planos")

        if intencion == "registro_cliente":
            if not any(p in texto for p in ["nombre", "empresa", "soy"]): faltantes.append("nombre_comercial")
            if not any(p in texto for p in ["comercial", "empresarial", "institucional", "taller", "hotel"]): faltantes.append("tipo_giro")
            if "rfc" not in texto: faltantes.append("rfc")
            if not any(p in texto for p in ["calle", "av", "direccion", "ubicado"]): faltantes.append("dirección_fiscal")

        return faltantes

    def _generar_respuesta_chatbot(self, intencion: str, cliente: Optional[Dict[str, Any]], productos: list, servicio: Optional[Dict[str, Any]], datos_faltantes: List[str]) -> str:
        # Mapeo amigable para el usuario final
        nombres_amigables = {
            "identificación_cliente": "el nombre de tu empresa o ID de cliente registrado",
            "producto_especifico": "los equipos o refacciones que necesitas",
            "tipo_de_servicio": "el tipo de servicio técnico (Preventivo, Correctivo o Instalación)",
            "descripción_de_la_falla": "un breve detalle de la falla o anomalía que presenta el sistema",
            "información_del_sitio_o_planos": "las dimensiones del lugar o si cuentas con planos hidráulicos",
            "nombre_comercial": "el nombre oficial de tu negocio o empresa",
            "tipo_giro": "si tu empresa es de giro Comercial, Empresarial o Institucional",
            "rfc": "tu RFC de facturación",
            "dirección_fiscal": "tu domicilio completo"
        }

        if datos_faltantes:
            faltas_str = " y ".join([nombres_amigables.get(d, d) for d in datos_faltantes])
            return f"¡Hola! Con gusto te apoyo con tu solicitud. Para poder procesarla adecuadamente en nuestro sistema experto, me faltaría que me proporciones: {faltas_str}. ¿Me podrías confirmar ese dato?"

        if intencion == "registro_cliente":
            return "¡Excelente! He recolectado todos tus datos fiscales de forma correcta. Ya puedo proceder a darte de alta en nuestra base de datos. Confirma con el operador para guardar tu registro."

        nombre_cliente = cliente["nombre"] if cliente else "estimado cliente"
        if intencion == "servicio":
            return f"Perfecto, {nombre_cliente}. He tomado nota de tu solicitud para el servicio de {servicio['nombre']}. La orden fue enviada al motor técnico para su preaprobación."
        if intencion == "compra_cotizacion":
            return f"Entendido, {nombre_cliente}. Registré la cotización de los materiales solicitados. Procederemos a verificar disponibilidad en almacén inmediatamente."
        if intencion == "mixta":
            return f"Recibido, {nombre_cliente}. Procesaremos tanto la adquisición de los equipos como la programación del servicio técnico de instalación."
        
        return "He recibido tu mensaje. Estoy analizando las especificaciones técnicas con el supervisor."