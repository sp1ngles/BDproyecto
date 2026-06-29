import psycopg2
import random
from config import DB_CONFIG


def procesar_ciclo_pagos_y_desembolsos(schema="public"):
    print(f"Iniciando ciclo transaccional (Con reglas de remesas) en '{schema}'...")
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {schema}, public;")

        query_prestamos = f"""
            SELECT p.id_prestamo, p.id_cliente, p.monto_aprobado, c.id_cuenta, cl.id_tipo_cliente
            FROM {schema}.prestamopersonal p
            JOIN {schema}.cuentabancaria c ON p.id_cliente = c.id_cliente
            JOIN {schema}.cliente cl ON p.id_cliente = cl.id_cliente
            WHERE p.estado_prestamo IN ('Aprobado', 'Vigente');
        """
        cursor.execute(query_prestamos)
        prestamos = cursor.fetchall()

        if not prestamos:
            print("No se encontraron préstamos aptos para simular transacciones.")
            return

        insert_query = f"""
            INSERT INTO {schema}.desembolso (id_desembolso, id_prestamo, id_cuenta, monto_desembolso, tipo_desembolso, estado_desembolso)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_desembolso) DO NOTHING;
        """

        desembolsos_cont = 0
        for p in prestamos:
            id_prestamo, id_cliente, monto, id_cuenta, id_tipo_cliente = p[0], p[1], p[2], p[3], p[4]

            if id_tipo_cliente in [3, 4]:
                # Segmentos altos (Nivel 3 y 4)
                tipo_transf = random.choice([
                    'Transf. CCE Exterior',
                    'Transf. Exterior',
                    'Remesa Soles Pref.',
                    'Remesa Dólares Cero'
                ])
            else:
                # Segmentos básicos (Nivel 1 y 2)
                tipo_transf = random.choice([
                    'Transf. CCE Nacional',
                    'Retiro PayPal',
                    'Remesa Soles',
                    'Remesa Cuenta Simple',
                    'Remesa Plin IBK'
                ])

            cursor.execute(insert_query, (id_prestamo, id_prestamo, id_cuenta, monto, tipo_transf, 'Ejecutado'))
            desembolsos_cont += 1

        connection.commit()
        print(f"-> ¡Éxito! Se completaron {desembolsos_cont} transacciones respetando las reglas de remesas.")
    except psycopg2.Error as error:
        print(f"ERROR: {error}")
        if connection: connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()


# ==============================================================================
# ALIAS DE COMPATIBILIDAD: Permite que cargar_todo.py lo importe con el otro nombre
# ==============================================================================
generar_ciclo_completo_pagos = procesar_ciclo_pagos_y_desembolsos

if __name__ == "__main__":
    procesar_ciclo_pagos_y_desembolsos()