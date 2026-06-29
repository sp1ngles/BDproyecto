import psycopg2
import random
from faker import Faker
from psycopg2.extras import execute_values
from config import DB_CONFIG

fake = Faker('es_ES')


def obtener_personas_libres(cursor, schema):
    # EL FIX DEL CICLO ANIDADO: NOT EXISTS
    cursor.execute(f"""
        SELECT p.id_persona FROM {schema}.persona p
        WHERE NOT EXISTS (SELECT 1 FROM {schema}.cliente c WHERE c.id_persona = p.id_persona)
          AND NOT EXISTS (SELECT 1 FROM {schema}.aval a WHERE a.id_persona = p.id_persona);
    """)
    return [r[0] for r in cursor.fetchall()]


def generar_e_insertar_avales(cantidad_registros, schema="public"):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {schema}, public;")

        personas = obtener_personas_libres(cursor, schema)
        if not personas:
            print("Error: No hay personas disponibles para ser Avales.")
            return

        registros_a_insertar = min(cantidad_registros, len(personas))
        print(f"Insertando en {schema}.aval {registros_a_insertar} registros por lotes...")

        insert_query = f"""
            INSERT INTO {schema}.aval (id_aval, id_persona, relacion_cliente, ingreso_mensual, empresa_laboral)
            VALUES %s
        """

        lote = []
        for i in range(1, registros_a_insertar + 1):
            id_persona = personas[i - 1]
            relacion = random.choice(['Familiar', 'Cónyuge', 'Socio', 'Amigo'])
            ingreso = round(random.uniform(1500.00, 8000.00), 2)
            empresa = fake.company()[:80]

            lote.append((i, id_persona, relacion, ingreso, empresa))

            if len(lote) >= 10000:
                execute_values(cursor, insert_query, lote)
                connection.commit()
                lote = []

        if lote:
            execute_values(cursor, insert_query, lote)
            connection.commit()

        print(f"¡Éxito! Se han insertado {registros_a_insertar} avales correctamente.")
    except psycopg2.Error as error:
        print(f"ERROR en Aval: {error}")
        if connection: connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()