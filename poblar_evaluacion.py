import psycopg2
import random
from datetime import timedelta
from config import DB_CONFIG


def obtener_datos_evaluacion(cursor, schema):
    cursor.execute(
        "SELECT id_solicitud, estado_solicitud, fecha_solicitud FROM {schema}.solicitud;".format(schema=schema))
    solicitudes = cursor.fetchall()
    cursor.execute("SELECT id_asesor FROM {schema}.asesor WHERE estado_asesor = 'Activo';".format(schema=schema))
    asesores = [r[0] for r in cursor.fetchall()]
    return solicitudes, asesores


def generar_e_insertar_evaluaciones(schema):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SET search_path TO {schema}, public;".format(schema=schema))

        solicitudes, asesores = obtener_datos_evaluacion(cursor, schema)
        if not solicitudes or not asesores:
            print("Error: Faltan solicitudes o asesores activos.")
            return

        print(f"Evaluando {len(solicitudes)} solicitudes en el sistema...")

        insert_query = """
            INSERT INTO {schema}.evaluacion (id_evaluacion, id_asesor, id_solicitud, resultado, capacidad_pago, estado_evaluacion, observaciones, fecha_evaluacion, puntaje_riesgo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """.format(schema=schema)

        for id_ev, sol in enumerate(solicitudes, start=1):
            id_solicitud, estado_sol, f_solicitud = sol[0], sol[1], sol[2]
            id_asesor = random.choice(asesores)

            # Mapeo lógico para no romper restricciones semánticas
            if estado_sol == 'Aprobada':
                resultado = 'Aprobado'
            elif estado_sol == 'Rechazada':
                resultado = 'Rechazado'
            else:
                resultado = 'Observado'

            capacidad_pago = round(random.uniform(1000.00, 5000.00), 2)
            f_evaluacion = f_solicitud + timedelta(days=random.randint(1, 4))
            puntaje_riesgo = round(random.uniform(5.00, 95.00), 2)

            cursor.execute(insert_query, (id_ev, id_asesor, id_solicitud, resultado, capacidad_pago, 'Completado',
                                          'Evaluación de riesgo crediticio estándar.', f_evaluacion, puntaje_riesgo))

        connection.commit()
        print("¡Éxito! Evaluaciones registradas.")
    except psycopg2.Error as error:
        print(f"ERROR en Evaluacion: {error}")
        if connection: connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()