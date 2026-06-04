import sqlite3
import os

RUTA_BD = os.path.join("bd", "sistema_incendio.db")

conexion = sqlite3.connect(RUTA_BD)
cursor = conexion.cursor()

print("\nPRODUCTOS REGISTRADOS:")
cursor.execute("SELECT id_producto, nombre, categoria, precio, stock FROM productos")

productos = cursor.fetchall()

for producto in productos:
    print(producto)

print("\nSERVICIOS REGISTRADOS:")
cursor.execute("SELECT id_servicio, nombre, costo FROM servicios")

servicios = cursor.fetchall()

for servicio in servicios:
    print(servicio)

print("\nCLIENTES REGISTRADOS:")
cursor.execute("SELECT id_cliente, nombre, tipo, cliente_frecuente FROM clientes")

clientes = cursor.fetchall()

for cliente in clientes:
    print(cliente)

conexion.close()