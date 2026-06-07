import re
from typing import Any, Dict, List, Optional

import db


# ============================================================
# agente_cliente.py
# Agente 1 - Atención al Cliente
#
# Función:
#   - Leer el mensaje del cliente.
#   - Detectar intención.
#   - Detectar cliente registrado.
#   - Detectar productos usando alias_productos.
#   - Detectar servicios.
#   - Detectar cantidades aproximadas.
#   - Marcar datos faltantes.
#
# Este agente NO calcula costos finales ni aplica reglas profundas.
# Eso le corresponde al Agente 2 / Motor de Inferencia.
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
                "respuesta_sugerida": "Por favor escribe una solicitud para poder analizarla."
            }

        intencion = self._detectar_intencion(mensaje)
        cliente = db.buscar_cliente_en_texto(mensaje)
        productos = self._detectar_productos(mensaje)
        servicio = db.buscar_servicio_en_texto(mensaje)
        servicio_foraneo = self._detectar_servicio_foraneo(mensaje)
        datos_faltantes = self._detectar_datos_faltantes(
            intencion=intencion,
            cliente=cliente,
            productos=productos,
            servicio=servicio,
            mensaje=mensaje
        )

        respuesta_sugerida = self._generar_respuesta_sugerida(
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

    # --------------------------------------------------------
    # DETECCIÓN DE INTENCIÓN
    # --------------------------------------------------------

    def _detectar_intencion(self, mensaje: str) -> str:
        texto = db.texto_normalizado(mensaje)

        palabras_registro = [
            "registrarme",
            "registrar cliente",
            "dar de alta",
            "alta de cliente",
            "nuevo cliente",
            "agregar cliente"
        ]

        palabras_servicio = [
            "servicio",
            "mantenimiento",
            "preventivo",
            "correctivo",
            "inspeccion",
            "revision",
            "instalacion",
            "instalar",
            "falla",
            "no funciona",
            "reparar",
            "goteo",
            "fuga"
        ]

        palabras_inventario = [
            "stock",
            "inventario",
            "disponible",
            "tienes",
            "hay existencia",
            "existencia"
        ]

        palabras_compra = [
            "comprar",
            "compra",
            "cotizar",
            "cotizacion",
            "precio",
            "necesito",
            "quiero",
            "vender",
            "pedido"
        ]

        es_registro = any(palabra in texto for palabra in palabras_registro)
        es_servicio = any(palabra in texto for palabra in palabras_servicio)
        es_inventario = any(palabra in texto for palabra in palabras_inventario)
        es_compra = any(palabra in texto for palabra in palabras_compra)

        if es_registro:
            return "registro_cliente"

        if es_servicio and es_compra:
            return "mixta"

        if es_servicio:
            return "servicio"

        if es_inventario:
            return "consulta_inventario"

        if es_compra:
            return "compra_cotizacion"

        return "general"

    # --------------------------------------------------------
    # DETECCIÓN DE PRODUCTOS Y CANTIDADES
    # --------------------------------------------------------

    def _detectar_productos(self, mensaje: str) -> List[Dict[str, Any]]:
        productos_base = db.buscar_productos_en_texto(mensaje)
        productos_detectados = []

        for producto in productos_base:
            cantidad = self._detectar_cantidad_cerca_de_alias(
                mensaje=mensaje,
                alias=producto["alias"]
            )

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
        """
        Detecta cantidades simples como:
            "3 sensores de flujo"
            "necesito 2 bombas jockey"
            "quiero 1 tablero de control"

        Si no detecta cantidad, regresa 1.
        """
        texto = db.texto_normalizado(mensaje)
        alias_norm = db.texto_normalizado(alias)

        posicion = texto.find(alias_norm)

        if posicion == -1:
            return 1

        texto_previo = texto[max(0, posicion - 40):posicion]

        patrones = [
            r"(\d+)\s*(piezas|pieza|pz|unidades|unidad|u)?\s*(de\s+)?$",
            r"(\d+)\s*$"
        ]

        for patron in patrones:
            coincidencia = re.search(patron, texto_previo)

            if coincidencia:
                try:
                    return max(1, int(coincidencia.group(1)))
                except ValueError:
                    return 1

        return 1

    # --------------------------------------------------------
    # DETECCIÓN DE UBICACIÓN / SERVICIO FORÁNEO
    # --------------------------------------------------------

    def _detectar_servicio_foraneo(self, mensaje: str) -> bool:
        texto = db.texto_normalizado(mensaje)

        palabras_foraneo = [
            "foraneo",
            "otro estado",
            "fuera del estado",
            "fuera de jalisco",
            "viajar",
            "traslado",
            "viaticos",
            "viatico"
        ]

        return any(palabra in texto for palabra in palabras_foraneo)

    # --------------------------------------------------------
    # DATOS FALTANTES
    # --------------------------------------------------------

    def _detectar_datos_faltantes(
        self,
        intencion: str,
        cliente: Optional[Dict[str, Any]],
        productos: List[Dict[str, Any]],
        servicio: Optional[Dict[str, Any]],
        mensaje: str
    ) -> List[str]:
        faltantes = []
        texto = db.texto_normalizado(mensaje)

        if intencion in ["compra_cotizacion", "servicio", "mixta", "consulta_inventario"]:
            if cliente is None:
                faltantes.append("cliente")

        if intencion in ["compra_cotizacion", "mixta", "consulta_inventario"]:
            if not productos:
                faltantes.append("producto")

        if intencion in ["servicio", "mixta"]:
            if servicio is None:
                faltantes.append("tipo_servicio")

            if servicio and servicio.get("tipo_servicio") == "Correctivo":
                palabras_falla = [
                    "falla",
                    "no funciona",
                    "no prende",
                    "no arranca",
                    "goteo",
                    "fuga",
                    "problema",
                    "presion",
                    "ruido"
                ]

                if not any(palabra in texto for palabra in palabras_falla):
                    faltantes.append("descripcion_falla")

            if servicio and servicio.get("tipo_servicio") == "Instalacion":
                palabras_sitio = [
                    "plano",
                    "planos",
                    "metros",
                    "area",
                    "sitio",
                    "ubicacion",
                    "tuberia",
                    "bodega",
                    "almacen"
                ]

                if not any(palabra in texto for palabra in palabras_sitio):
                    faltantes.append("informacion_del_sitio")

        if intencion == "registro_cliente":
            datos_registro = {
                "nombre_cliente": ["nombre", "empresa", "cliente"],
                "tipo_cliente": ["comercial", "empresarial", "institucional"],
                "rfc": ["rfc"],
                "direccion": ["direccion", "ubicacion", "domicilio"],
                "equipo_instalado": ["bomba", "tablero", "equipo", "sistema"]
            }

            for dato, palabras in datos_registro.items():
                if not any(palabra in texto for palabra in palabras):
                    faltantes.append(dato)

        return faltantes

    # --------------------------------------------------------
    # RESPUESTA SUGERIDA
    # --------------------------------------------------------

    def _generar_respuesta_sugerida(
        self,
        intencion: str,
        cliente: Optional[Dict[str, Any]],
        productos: List[Dict[str, Any]],
        servicio: Optional[Dict[str, Any]],
        datos_faltantes: List[str]
    ) -> str:
        if datos_faltantes:
            return (
                "Detecté la solicitud, pero faltan algunos datos para continuar: "
                + ", ".join(datos_faltantes)
                + "."
            )

        if intencion == "registro_cliente":
            return "Detecté una intención de registro de nuevo cliente. Se puede enviar al flujo de alta."

        if intencion == "servicio":
            return "Detecté una solicitud de servicio. La información puede enviarse al motor de inferencia."

        if intencion == "compra_cotizacion":
            return "Detecté una solicitud de compra o cotización. La información puede enviarse al motor de inferencia."

        if intencion == "mixta":
            return "Detecté una solicitud con productos y servicio. Conviene validar ambos elementos con el motor de inferencia."

        if intencion == "consulta_inventario":
            return "Detecté una consulta de inventario. Se puede validar disponibilidad en la base de datos."

        return "Detecté un mensaje general. Puede requerir más información para clasificarlo correctamente."


# ============================================================
# PRUEBA RÁPIDA
# Ejecuta:
#   python src/agente_cliente.py
# ============================================================

if __name__ == "__main__":
    agente = AgenteAtencionCliente()

    ejemplos = [
        "Hola, soy Hotel Guadalajara y necesito 2 sensores de flujo.",
        "Soy Taller Mecánico Ramírez, necesito mantenimiento correctivo porque la bomba tiene fuga.",
        "Quiero instalar un sistema contra incendio en otro estado.",
        "Soy nuevo cliente y quiero registrarme."
    ]

    for ejemplo in ejemplos:
        print("\nMENSAJE:", ejemplo)
        resultado = agente.analizar_mensaje(ejemplo)
        print(resultado)
