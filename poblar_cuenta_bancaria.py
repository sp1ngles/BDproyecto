import psycopg2
import random
from psycopg2.extras import execute_values
from config import DB_CONFIG

# Esta función ahora recibirá un float, por lo que las comparaciones funcionarán perfecto
def obtener_nivel_sueldo(ingreso):
    if ingreso >= 18000.00: return "Nivel 4"
    elif ingreso >= 7500.00: return "Nivel 3"
    elif ingreso >= 3500.00: return "Nivel 2"
    else: return "Nivel 1"

def generar_e_insertar_cuentas(schema="public"):
    print(f"Iniciando población de cuentabancaria (Fix: Conversión Decimal a Float)...")
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {schema}, public;")

        cursor.execute(f"SELECT id_cliente, id_tipo_cliente, ingreso_mensual FROM {schema}.cliente;")
        clientes = cursor.fetchall()
        if not clientes: return

        insert_query = """
            INSERT INTO cuentabancaria (id_cuenta, id_cliente, numero_cuenta, cci, saldo, estado_cuenta, tipo_cuenta)
            VALUES %s ON CONFLICT (id_cuenta) DO NOTHING;
        """

        lote = []
        id_cuenta_actual = 1

        for id_cliente, id_tipo_cliente, ingreso_bd in clientes:
            # 🌟 AQUÍ ESTÁ EL FIX: Convertimos el Decimal de Postgres a float de Python 🌟
            ingreso = float(ingreso_bd) if ingreso_bd is not None else 1025.0

            num_cuenta = f"191-{random.randint(10000000, 99999999)}-0-{random.randint(10, 99)}"
            cci = "003" + "".join(random.choices("0123456789", k=17))

            # Productos basados en el segmento corporativo/retail
            if id_tipo_cliente == 3: # Corporate
                tipo_base = random.choice(['Cuenta Corriente Corporativa', 'Cuenta Recaudadora', 'Depósito a Plazo Fijo Empresa'])
                saldo = round(random.uniform(50000.00, max(50000.00, ingreso * 2)), 2)
            elif id_tipo_cliente == 2: # Negocios
                tipo_base = random.choice(['Cuenta Negocios Interbank', 'Cuenta Corriente', 'Cuenta Sueldo'])
                saldo = round(random.uniform(5000.00, max(5000.00, ingreso)), 2)
            else: # Retail
                tipo_base = random.choice(['Cuenta Sueldo', 'Cuenta Joven', 'Cuenta Simple Digital'])
                saldo = round(random.uniform(50.00, max(50.00, ingreso)), 2)

            # Candado estricto: Niveles solo para Cuenta Sueldo
            if tipo_base == 'Cuenta Sueldo':
                tipo_final = f"Cuenta Sueldo ({obtener_nivel_sueldo(ingreso)})"
            else:
                tipo_final = tipo_base

            lote.append((id_cuenta_actual, id_cliente, num_cuenta, cci, saldo, 'Activa', tipo_final))
            id_cuenta_actual += 1

            if len(lote) >= 10000:
                execute_values(cursor, insert_query, lote)
                connection.commit()
                lote = []

        if lote:
            execute_values(cursor, insert_query, lote)
            connection.commit()

        print("¡Éxito! Cuentas bancarias generadas sin errores de tipo de datos.")
    except psycopg2.Error as error:
        print(f"ERROR en Cuentas: {error}")
        if connection: connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()