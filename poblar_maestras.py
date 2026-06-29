import psycopg2
from psycopg2.extras import execute_values
from config import DB_CONFIG


def cargar_tablas_maestras(schema="public"):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {schema}, public;")

        print(f"Poblando tablas maestras (3 Segmentos Exactos) en '{schema}'...")
        cursor.execute(f"TRUNCATE TABLE {schema}.tipocliente RESTART IDENTITY CASCADE;")

        # 3 Tipos basados exactamente en tus requisitos corporativos
        tipos_cliente = [
            (1, 'Banca Personas (Retail)', 'Individuos >18 años con DNI/CE, sustento de ingresos y buen historial.',
             25000, 15),
            (2, 'Pequeña Empresa (Banca Negocios)',
             'RUC activo, ventas < 5M soles, max 2 representantes, antigüedad 6-12 meses.', 150000, 12),
            (3, 'Clientes Comerciales (Corporate)',
             'Corporaciones grandes. Requiere escritura pública y estados financieros auditados.', 2000000, 8)
        ]

        insert_query = f"""
            INSERT INTO {schema}.tipocliente (id_tipo_cliente, nombre_tipo, descripcion, monto_maximo_prestamo, tasa_interes_base) 
            VALUES %s ON CONFLICT DO NOTHING;
        """
        execute_values(cursor, insert_query, tipos_cliente)

        connection.commit()
        print("¡Tablas Maestras actualizadas con los 3 segmentos bancarios!")
    except psycopg2.Error as error:
        print(f"ERROR en Maestras: {error}")
        if connection: connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()