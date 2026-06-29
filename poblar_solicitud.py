# poblar_solicitud.py
import psycopg2
import random
from faker import Faker
from config import DB_CONFIG

fake = Faker('es_ES')


def obtener_clientes_existentes(cursor, schema):
    cursor.execute("SELECT id_cliente, fecha_registro FROM {schema}.cliente;".format(schema=schema))
    return cursor.fetchall()


def generar_e_insertar_solicitudes(cantidad_registros, schema):
    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SET search_path TO {schema}, public;".format(schema=schema))

        clientes_data = obtener_clientes_existentes(cursor, schema)

        if not clientes_data:
            print("Error: La tabla 'cliente' está vacía.")
            return

        print(f"Insertando en la tabla {schema}.solicitud {cantidad_registros} registros...")

        insert_query = """
            INSERT INTO {schema}.solicitud (id_solicitud, id_cliente, estado_solicitud, motivo_prestamo, monto_solicitud, historial_crediticio, fecha_solicitud)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """.format(schema=schema)

        for i in range(1, cantidad_registros + 1):
            cliente = random.choice(clientes_data)
            id_cliente = cliente[0]
            fecha_registro_cliente = cliente[1]

            estado_solicitud = random.choice(['Pendiente', 'Aprobada', 'Rechazada'])
            motivo_prestamo = random.choice(['Consumo', 'Capital de Trabajo', 'Vehicular', 'Salud'])[:100]
            monto_solicitud = round(random.uniform(500.00, 50000.00), 2)
            historial_crediticio = "El cliente cuenta con un comportamiento de pago óptimo en el sistema financiero."

            # La solicitud debe ser posterior a la fecha en que se registró el cliente
            fecha_solicitud = fake.date_between(start_date=fecha_registro_cliente, end_date='today')

            cursor.execute(insert_query,
                           (i, id_cliente, estado_solicitud, motivo_prestamo, monto_solicitud, historial_crediticio,
                            fecha_solicitud))

        connection.commit()
        print(f"¡Éxito! Se han insertado {cantidad_registros} solicitudes correctamente.")

    except psycopg2.Error as error:
        print(f"ERROR al insertar en Solicitud: {error}")
        if connection: connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()