import sqlite3
import json
import os

RUTA_BD = os.path.join("bd", "sistema_incendio.db")

def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)

conexion = sqlite3.connect(RUTA_BD)
cursor = conexion.cursor()

# =========================
# CARGAR CLIENTES
# =========================
clientes = cargar_json(os.path.join("datos", "clientes.json"))

for cliente in clientes:
    cursor.execute("""
    INSERT OR REPLACE INTO clientes (
        id_cliente,
        nombre,
        tipo,
        cliente_frecuente,
        ultima_compra_dias
    ) VALUES (?, ?, ?, ?, ?)
    """, (
        cliente["id_cliente"],
        cliente["nombre"],
        cliente["tipo"],
        1 if cliente["cliente_frecuente"] else 0,
        cliente["ultima_compra_dias"]
    ))

# =========================
# CARGAR PRODUCTOS
# =========================
productos = cargar_json(os.path.join("datos", "productos.json"))

for producto in productos:
    cursor.execute("""
    INSERT OR REPLACE INTO productos (
        id_producto,
        nombre,
        categoria,
        potencia_hp,
        precio,
        stock
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        producto["id_producto"],
        producto["nombre"],
        producto["categoria"],
        producto["potencia_hp"],
        producto["precio"],
        producto["stock"]
    ))

# =========================
# CARGAR SERVICIOS
# =========================
servicios = cargar_json(os.path.join("datos", "servicios.json"))

for servicio in servicios:
    cursor.execute("""
    INSERT OR REPLACE INTO servicios (
        id_servicio,
        nombre,
        costo,
        duracion_horas,
        descripcion
    ) VALUES (?, ?, ?, ?, ?)
    """, (
        servicio["id_servicio"],
        servicio["nombre"],
        servicio["costo"],
        servicio["duracion_horas"],
        servicio["descripcion"]
    ))

conexion.commit()
conexion.close()

print("Datos cargados correctamente en la base de datos.")