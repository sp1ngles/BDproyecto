import psycopg2
import random
from datetime import timedelta
from psycopg2.extras import execute_values
from config import DB_CONFIG


def poblar_requisitos_y_seguros(schema="public"):
    print("\n--- Iniciando población de Requisitos y Seguros ---")
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(f"SET search_path TO {schema}, public;")

        # 1. POBLAR REQUISITOS (Asociados a las Solicitudes)
        cursor.execute("SELECT id_solicitud, fecha_solicitud FROM solicitud;")
        solicitudes = cursor.fetchall()

        if solicitudes:
            print("Generando entrega de documentos (Requisitos)...")
            req_data = []
            id_req = 1
            docs_base = [('Copia de DNI', True), ('Recibo de Servicios', True), ('Sustento de Ingresos', True),
                         ('Ficha RUC', False)]

            for sol in solicitudes:
                id_sol, f_sol = sol
                # Cada solicitud tendrá entre 2 y 3 requisitos presentados
                docs_presentados = random.sample(docs_base, random.randint(2, 3))

                for doc, es_obligatorio in docs_presentados:
                    estado = random.choice(['Entregado', 'Entregado', 'Pendiente'])
                    f_entrega = f_sol + timedelta(days=random.randint(0, 5)) if estado == 'Entregado' else None
                    req_data.append(
                        (id_req, f"Documento: {doc} validado", doc, estado, f_entrega, es_obligatorio, id_sol))
                    id_req += 1

            execute_values(cursor, """
                                   INSERT INTO requisito (id_requisito, descripcion, nombre_requisito, estado_entrega,
                                                          fecha_entrega, obligatorio, id_solicitud)
                                   VALUES %s ON CONFLICT DO NOTHING;
                                   """, req_data)

        # 2. POBLAR SEGUROS (Asociados a las Cuotas)
        cursor.execute("SELECT id_cuota, monto_total FROM cuota WHERE estado_cuota IN ('Pagada', 'Pendiente');")
        cuotas = cursor.fetchall()

        if cuotas:
            print("Asignando Seguros de Desgravamen a las cuotas...")
            seguro_data = []
            id_seg = 1

            # Solo el 80% de las cuotas tendrán seguro (para dar variedad)
            cuotas_con_seguro = random.sample(cuotas, int(len(cuotas) * 0.8))

            for cuota in cuotas_con_seguro:
                id_cuota, monto_cuota = cuota
                monto_seguro = round(float(monto_cuota) * 0.015, 2)  # Seguro es 1.5% de la cuota
                seguro_data.append(
                    (id_seg, id_cuota, 'Seguro de Desgravamen - Cobertura Total', monto_seguro, 'Desgravamen', 'Activo',
                     0.00))
                id_seg += 1

                # Insertar en lotes para no saturar la memoria
                if len(seguro_data) >= 5000:
                    execute_values(cursor,
                                   "INSERT INTO seguro (id_seguro, id_cuota, cobertura, monto_seguro, tipo_seguro, estado_seguro, monto_devolucion) VALUES %s ON CONFLICT DO NOTHING;",
                                   seguro_data)
                    seguro_data = []

            if seguro_data:
                execute_values(cursor,
                               "INSERT INTO seguro (id_seguro, id_cuota, cobertura, monto_seguro, tipo_seguro, estado_seguro, monto_devolucion) VALUES %s ON CONFLICT DO NOTHING;",
                               seguro_data)

        connection.commit()
        print(" ¡Éxito! Tablas Requisito y Seguro pobladas correctamente.")

    except psycopg2.Error as error:
        print(f"ERROR: {error}")
        if connection: connection.rollback()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()


if __name__ == "__main__":
    poblar_requisitos_y_seguros()