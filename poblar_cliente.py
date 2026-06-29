import psycopg2
import random
from psycopg2.extras import execute_values
from config import DB_CONFIG


def clasificar_segmento_bancario(ingreso):
    if ingreso >= 80000.00:
        return 3  # Corporate (Alta facturación)
    elif ingreso >= 12000.00:
        return 2  # Pequeña Empresa (Facturación moderada)
    else:
        return 1  # Retail / Banca Personas


def generar_e_insertar_clientes(cantidad_registros=100, schema="public"):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {schema}, public;")

        cursor.execute(f"SELECT id_persona FROM {schema}.persona;")
        personas = [r[0] for r in cursor.fetchall()]
        random.shuffle(personas)

        print(f"Insertando {min(cantidad_registros, len(personas))} clientes por lotes...")

        insert_query = f"""
            INSERT INTO {schema}.cliente (id_cliente, id_persona, id_tipo_cliente, celular, ingreso_mensual, score_crediticio, estado_cliente, fecha_registro)
            VALUES %s ON CONFLICT (id_cliente) DO NOTHING;
        """

        lote = []
        for i in range(1, min(cantidad_registros, len(personas)) + 1):
            id_persona = personas[i - 1]

            # Generamos ingresos variados para poblar todos los segmentos
            selector = random.random()
            if selector < 0.70:
                ingreso = round(random.uniform(1025.00, 11999.00), 2)
            elif selector < 0.95:
                ingreso = round(random.uniform(12000.00, 79999.00), 2)
            else:
                ingreso = round(random.uniform(80000.00, 500000.00), 2)

            id_tipo = clasificar_segmento_bancario(ingreso)
            celular = "9" + "".join(random.choices("0123456789", k=8))
            score = round(random.uniform(300.00, 850.00), 2)

            lote.append((i, id_persona, id_tipo, celular, ingreso, score, 'Activo', '2023-01-01'))

            if len(lote) >= 10000:
                execute_values(cursor, insert_query, lote)
                connection.commit()
                lote = []

        if lote:
            execute_values(cursor, insert_query, lote)
            connection.commit()

        print("¡Éxito! Clientes clasificados en Retail, Negocios y Corporate correctamente.")
    except psycopg2.Error as error:
        print(f"ERROR en Cliente: {error}")
        if connection: connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()