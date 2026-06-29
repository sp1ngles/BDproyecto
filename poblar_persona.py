# poblar_persona.py
import psycopg2
import random
from faker import Faker
from config import DB_CONFIG

fake = Faker('es_ES')


def generar_e_insertar_personas(cantidad_registros, schema):
    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SET search_path TO {schema}, public;".format(schema=schema))

        print(f"Insertando en la tabla {schema}.persona {cantidad_registros} registros...")

        insert_query = """
            INSERT INTO {schema}.persona (id_persona, tipo_documento, nombre_documento, genero, nombre, apellido, f_nacimiento, correo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """.format(schema=schema)

        for i in range(1, cantidad_registros + 1):
            genero = random.choice(['Masculino', 'Femenino', 'Otro'])
            nombre = fake.first_name_male() if genero == 'Masculino' else fake.first_name_female()
            apellido = f"{fake.last_name()} {fake.last_name()}"

            tipo_doc = random.choice(['DNI', 'CE'])
            # Asegurar longitud permitida en VARCHAR(20)
            num_doc = str(random.randint(10000000, 99999999)) if tipo_doc == 'DNI' else str(
                random.randint(100000000, 999999999))

            # i asegura que el correo sea UNIQUE obligatoriamente
            correo = f"{nombre.lower()}.{fake.word()}{i}@ejemplo.com"[:80]
            f_nacimiento = fake.date_of_birth(minimum_age=18, maximum_age=70)

            cursor.execute(insert_query, (i, tipo_doc, num_doc, genero, nombre, apellido, f_nacimiento, correo))

        connection.commit()
        print(f"¡Éxito! Se han insertado {cantidad_registros} personas correctamente.")

    except psycopg2.Error as error:
        print(f"ERROR al insertar en Persona: {error}")
        if connection:
            connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()