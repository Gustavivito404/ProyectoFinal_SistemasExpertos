from agente_cliente import AgenteAtencionCliente


agente = AgenteAtencionCliente()

mensaje = input("Escribe un mensaje de cliente: ")

resultado = agente.analizar_mensaje(mensaje)

print("\n===== RESULTADO DEL AGENTE 1 =====")
print("Intención:", resultado["intencion"])
print("Cliente:", resultado["cliente_detectado"]["nombre"] if resultado["cliente_detectado"] else "No detectado")
print("Servicio:", resultado["servicio_detectado"]["nombre"] if resultado["servicio_detectado"] else "No detectado")
print("Servicio foráneo:", resultado["servicio_foraneo"])

print("\nProductos detectados:")
if resultado["productos_detectados"]:
    for producto in resultado["productos_detectados"]:
        print(f"- {producto['cantidad']} x {producto['nombre']} ({producto['alias_detectado']})")
else:
    print("- Ninguno")

print("\nDatos faltantes:")
if resultado["datos_faltantes"]:
    for dato in resultado["datos_faltantes"]:
        print(f"- {dato}")
else:
    print("- Ninguno")

print("\nRespuesta sugerida:")
print(resultado["respuesta_sugerida"])
