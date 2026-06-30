import psycopg2
import random
from faker import Faker
from psycopg2.extras import execute_values
from config import DB_CONFIG

fake = Faker('es_ES')


def generar_e_insertar_personas(cantidad_registros, schema="public"):
    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {schema}, public;")

        print(f"Insertando en la tabla {schema}.persona {cantidad_registros} registros por lotes...")

        insert_query = f"""
            INSERT INTO {schema}.persona (id_persona, tipo_documento, nombre_documento, genero, nombre, apellido, f_nacimiento, correo)
            VALUES %s
        """

        lote = []
        for i in range(1, cantidad_registros + 1):
            genero = random.choice(['Masculino', 'Femenino', 'Otro'])
            nombre = fake.first_name_male() if genero == 'Masculino' else fake.first_name_female()
            apellido = f"{fake.last_name()} {fake.last_name()}"

            tipo_doc = random.choice(['DNI', 'CE'])

            # --- NUEVA LÓGICA DE DNI ÚNICO ---
            if tipo_doc == 'DNI':
                num_doc = str(10000000 + i)
            else:
                num_doc = str(100000000 + i)
            # ---------------------------------

            correo = f"{nombre.lower()[:3]}.{fake.word()[:5]}{i}{random.randint(100, 999)}@ejemplo.com"[:80]
            f_nacimiento = fake.date_of_birth(minimum_age=18, maximum_age=70)

            lote.append((i, tipo_doc, num_doc, genero, nombre, apellido, f_nacimiento, correo))

            if len(lote) >= 10000:
                execute_values(cursor, insert_query, lote)
                connection.commit()
                lote = []

        if lote:
            execute_values(cursor, insert_query, lote)
            connection.commit()

        print(f"¡Éxito! Se han insertado {cantidad_registros} personas rápidamente.")

    except psycopg2.Error as error:
        print("\n" + "=" * 50)
        print(f"🚨 ERROR FATAL AL INSERTAR PERSONAS: \n{error}")
        print("=" * 50 + "\n")
        if connection:
            connection.rollback()
        raise Exception("Se detuvo el proceso por un error en Persona.")

    finally:
        if cursor: cursor.close()
        if connection: connection.close()