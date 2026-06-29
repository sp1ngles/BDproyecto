import psycopg2
import random
import traceback
from faker import Faker
from psycopg2.extras import execute_values
from config import DB_CONFIG

fake = Faker('es_ES')


def generar_e_insertar_prestamos(schema="public", cantidad=2500):
    print(f"--- Iniciando población de PrestamoPersonal ({cantidad} registros) ---")
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {schema}, public;")

        # 1. Obtener tasas válidas desde la tabla Tasa
        cursor.execute(f"SELECT id_tasa FROM {schema}.Tasa;")
        tasas = [r[0] for r in cursor.fetchall()]

        if not tasas:
            print(" La tabla 'Tasa' está vacía. Insertando tasas por defecto para rescatar el proceso...")
            # Insertamos un par de tasas maestras rápido si estuviera vacía
            execute_values(cursor,
                           f"INSERT INTO {schema}.Tasa (id_tasa, tipo_tasa, frecuencia, valor_tasa) VALUES %s ON CONFLICT DO NOTHING;",
                           [
                               (1, 'Efectiva Anual', 'Anual', 15.50),
                               (2, 'Efectiva Mensual', 'Mensual', 1.20)
                           ])
            connection.commit()
            tasas = [1, 2]

        # 2. Buscar evaluaciones cuyo resultado sea estrictamente 'Aprobado' (como pide tu CHECK)
        cursor.execute(f"""
            SELECT e.id_evaluacion, s.id_cliente, c.id_tipo_cliente
            FROM {schema}.Evaluacion e
            JOIN {schema}.Solicitud s ON e.id_solicitud = s.id_solicitud
            JOIN {schema}.Cliente c ON s.id_cliente = c.id_cliente
            WHERE e.resultado = 'Aprobado';
        """)
        evaluaciones_aprobadas = cursor.fetchall()

        if not evaluaciones_aprobadas:
            print(" No se encontraron Evaluaciones con resultado 'Aprobado'.")
            print(" Ejecuta el pipeline completo (cargar_todo.py) para asegurar el flujo correcto.")
            return

        # 3. Traer avales disponibles (opcional, ya que id_aval permite NULL en tu DDL)
        cursor.execute(f"SELECT id_aval FROM {schema}.Aval;")
        avales = [r[0] for r in cursor.fetchall()]

        # 4. Definir Query en el ORDEN EXACTO del CREATE TABLE de tu diseño:
        # (id_prestamo, id_cliente, id_evaluacion, id_aval, id_tasa, monto_aprobado, fecha_inicio, plazo_meses, estado_prestamo)
        insert_query = f"""
            INSERT INTO {schema}.PrestamoPersonal 
            (id_prestamo, id_cliente, id_evaluacion, id_aval, id_tasa, monto_aprobado, fecha_inicio, plazo_meses, estado_prestamo)
            VALUES %s ON CONFLICT (id_prestamo) DO NOTHING;
        """

        random.shuffle(evaluaciones_aprobadas)
        limite = min(cantidad, len(evaluaciones_aprobadas))

        lote = []
        for i in range(1, limite + 1):
            id_evaluacion, id_cliente, id_tipo_cliente = evaluaciones_aprobadas[i - 1]

            # Lógica de montos según TipoCliente
            if id_tipo_cliente == 3:  # Corporate
                monto = round(random.uniform(50000.00, 200000.00), 2)
                plazo = random.choice([36, 48, 60])
            elif id_tipo_cliente == 2:  # Negocios
                monto = round(random.uniform(5000.00, 49999.00), 2)
                plazo = random.choice([12, 18, 24])
            else:  # Retail
                monto = round(random.uniform(300.00, 4999.00), 2)
                plazo = random.choice([3, 6, 12])

            f_inicio = fake.date_between(start_date='-1y', end_date='today')
            estado = random.choice(['Vigente', 'Cancelado'])  # Estados válidos
            id_tasa = random.choice(tasas)
            id_aval = random.choice(avales) if (avales and random.random() > 0.7) else None

            # Tupla estructurada idéntica a las columnas declaradas arriba
            lote.append((i, id_cliente, id_evaluacion, id_aval, id_tasa, monto, f_inicio, plazo, estado))

            if len(lote) >= 1000:
                execute_values(cursor, insert_query, lote)
                connection.commit()
                lote = []

        if lote:
            execute_values(cursor, insert_query, lote)
            connection.commit()

        print(f" ¡Éxito! Se insertaron {limite} préstamos personales enlazados con Tasa y Evaluación.")

    except psycopg2.Error as error:
        print("\n ERROR GRAVE EN LA BASE DE DATOS (POSTGRESQL) ")
        print("Detalle del error:")
        print(error)
        if connection: connection.rollback()

    except Exception as e:
        print("\n ERROR INTERNO EN PYTHON ")
        print(traceback.format_exc())

    finally:
        if cursor: cursor.close()
        if connection: connection.close()


if __name__ == "__main__":
    generar_e_insertar_prestamos(schema="public", cantidad=2500)