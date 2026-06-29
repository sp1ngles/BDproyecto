import psycopg2
import random
from datetime import timedelta, date
from psycopg2.extras import execute_values
from config import DB_CONFIG


def poblar_fase_retorno(schema="public"):
    print(f"\n--- Iniciando población de Cronogramas, Cuotas, Pagos y Moras ---")
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {schema}, public;")

        # 1. Asegurar que existan Medios de Pago
        cursor.execute("SELECT id_medio_pago FROM mediopago;")
        medios = cursor.fetchall()
        if not medios:
            print("Insertando catálogos de Medios de Pago...")
            medios_data = [
                (1, 'App Móvil', 'Pago rápido desde la app del banco', 'Activo'),
                (2, 'Ventanilla', 'Pago presencial en agencia', 'Activo'),
                (3, 'Cargo Automático', 'Débito directo de la cuenta', 'Activo')
            ]
            execute_values(cursor,
                           "INSERT INTO mediopago (id_medio_pago, nombre_medio_pago, descripcion, estado_medio_pago) VALUES %s ON CONFLICT DO NOTHING;",
                           medios_data)
            medios_ids = [1, 2, 3]
        else:
            medios_ids = [m[0] for m in medios]

        # 2. Seleccionar SOLO los préstamos que ya fueron desembolsados exitosamente
        cursor.execute("""
                       SELECT p.id_prestamo, p.plazo_meses, p.monto_aprobado, p.fecha_inicio
                       FROM prestamopersonal p
                                JOIN desembolso d ON p.id_prestamo = d.id_prestamo;
                       """)
        prestamos = cursor.fetchall()

        if not prestamos:
            print("⚠️ No hay préstamos desembolsados para cobrar.")
            return

        crono_data, cuota_data, pago_data, mora_data = [], [], [], []
        id_crono, id_cuota, id_pago, id_mora = 1, 1, 1, 1
        hoy = date.today()

        for p in prestamos:
            id_prestamo, plazo, monto, f_inicio = p

            # Generar el Cronograma del Préstamo
            crono_data.append((id_crono, id_prestamo, f_inicio, plazo, 'Mensual', 'Cuota Fija', 'Activo'))

            # Cálculo simple de cuota (Monto + 15% interés aprox / meses)
            monto_cuota = round((float(monto) * 1.15) / plazo, 2)

            for n in range(1, plazo + 1):
                f_venc = f_inicio + timedelta(days=30 * n)

                # Regla de Negocio: Simular comportamiento de pago
                if f_venc < hoy:
                    # La cuota ya venció, veamos si el cliente pagó o se atrasó
                    pago_puntual = random.random() > 0.35  # 65% paga a tiempo

                    if pago_puntual:
                        f_pago = f_venc - timedelta(days=random.randint(0, 3))  # Pagó días antes
                        cuota_data.append((id_cuota, id_crono, monto_cuota, f_venc, f_pago, n, 'Pagada'))

                        # Registrar la transacción de Pago
                        pago_data.append(
                            (id_pago, id_cuota, random.choice(medios_ids), n, monto_cuota, f_pago, 'Regular',
                             f'OP-{random.randint(1000, 9999)}', 'Procesado'))
                        id_pago += 1
                    else:
                        # Moroso detectado!
                        cuota_data.append((id_cuota, id_crono, monto_cuota, f_venc, None, n, 'Pendiente'))

                        # Generar la penalidad de Mora
                        dias_atraso = (hoy - f_venc).days
                        monto_mora = round(dias_atraso * 2.50, 2)  # S/. 2.50 por cada día de atraso
                        mora_data.append((id_mora, id_cuota, dias_atraso, monto_mora, hoy, 0))
                        id_mora += 1
                else:
                    # Es una cuota del futuro, aún no vence
                    cuota_data.append((id_cuota, id_crono, monto_cuota, f_venc, None, n, 'Pendiente'))

                id_cuota += 1
            id_crono += 1

        # 3. Inserciones Masivas a la Base de Datos
        print("Guardando Cronogramas...")
        execute_values(cursor,
                       "INSERT INTO cronogramapagos (id_cronograma, id_prestamo, fecha_generacion, nro_cuotas, periodicidad, tipo_cronograma, estado_cronograma) VALUES %s ON CONFLICT DO NOTHING;",
                       crono_data)

        print("Generando miles de Cuotas...")
        for i in range(0, len(cuota_data), 5000):
            execute_values(cursor,
                           "INSERT INTO cuota (id_cuota, id_cronograma, monto_total, fecha_vencimiento, fecha_pago, nro_cuota, estado_cuota) VALUES %s ON CONFLICT DO NOTHING;",
                           cuota_data[i:i + 5000])

        if pago_data:
            print("Procesando Pagos realizados...")
            for i in range(0, len(pago_data), 5000):
                execute_values(cursor,
                               "INSERT INTO pago (id_pago, id_cuota, id_medio_pago, nro_cuota, monto_pago, fecha_pago, tipo_pago, numero_operacion, estado_pago) VALUES %s ON CONFLICT DO NOTHING;",
                               pago_data[i:i + 5000])

        if mora_data:
            print("Aplicando Moras y Penalidades a deudores...")
            for i in range(0, len(mora_data), 5000):
                execute_values(cursor,
                               "INSERT INTO mora (id_mora, id_cuota, dias_atraso, monto_mora, fecha_calculo, dias_gracia) VALUES %s ON CONFLICT DO NOTHING;",
                               mora_data[i:i + 5000])

        connection.commit()
        print(
            f"✅ ¡Fase Final Completada! Se generaron {len(crono_data)} cronogramas con {len(cuota_data)} cuotas, {len(pago_data)} pagos efectivos y {len(mora_data)} moras.")

    except psycopg2.Error as error:
        print("\n❌ ERROR GRAVE EN POSTGRESQL ❌")
        print(error)
        if connection: connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()


if __name__ == "__main__":
    poblar_fase_retorno()