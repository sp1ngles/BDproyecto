import psycopg2
import random
from faker import Faker
from psycopg2.extras import execute_values
from config import DB_CONFIG

fake = Faker('es_ES')


def obtener_personas_disponibles(cursor, schema):
    # EL FIX DEL CICLO ANIDADO: Usamos NOT EXISTS para velocidad ultra rápida
    cursor.execute(f"""
        SELECT p.id_persona FROM {schema}.persona p
        WHERE NOT EXISTS (SELECT 1 FROM {schema}.cliente c WHERE c.id_persona = p.id_persona)
          AND NOT EXISTS (SELECT 1 FROM {schema}.aval a WHERE a.id_persona = p.id_persona)
          AND NOT EXISTS (SELECT 1 FROM {schema}.asesor aser WHERE aser.id_persona = p.id_persona);
    """)
    return [r[0] for r in cursor.fetchall()]


def generar_e_insertar_asesores(cantidad_registros, schema="public"):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {schema}, public;")

        personas = obtener_personas_disponibles(cursor, schema)
        if not personas:
            print("Error: No hay personas libres para asignar como Asesores.")
            return

        registros_a_insertar = min(cantidad_registros, len(personas))
        print(f"Insertando en {schema}.asesor {registros_a_insertar} registros por lotes...")

        insert_query = f"""
            INSERT INTO {schema}.asesor (id_asesor, id_persona, sueldo, fecha_contratacion, estado_asesor)
            VALUES %s
        """

        lote = []
        for i in range(1, registros_a_insertar + 1):
            id_persona = personas[i - 1]
            sueldo = round(random.uniform(2500.00, 6500.00), 2)
            fecha_contratacion = fake.date_between(start_date='-5y', end_date='-1y')
            estado = random.choice(['Activo', 'Inactivo'])

            lote.append((i, id_persona, sueldo, fecha_contratacion, estado))

            if len(lote) >= 10000:
                execute_values(cursor, insert_query, lote)
                connection.commit()
                lote = []

        if lote:
            execute_values(cursor, insert_query, lote)
            connection.commit()

        print(f"¡Éxito! Se han insertado {registros_a_insertar} asesores en milisegundos.")
    except psycopg2.Error as error:
        print(f"ERROR en Asesor: {error}")
        if connection: connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()