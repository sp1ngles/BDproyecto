import psycopg2
from psycopg2.extras import execute_values  # Importamos para optimización en bloque

DB_CONFIG = {
    "dbname": "ProyectoBD",
    "user": "postgres",
    "password": "pepito",
    "host": "localhost",
    "port": "5432"
}

def generar_tipo_cliente(schema="public"):
    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        cursor.execute(
            f"SET search_path TO {schema}, public;"
        )

        # Los 3 Tipos de Cliente oficiales basados exactamente en tus requerimientos de negocio
        datos = [
            (
                1,
                "Banca Personas (Retail)",
                "Individuos >18 anos con DNI/CE, sustento de ingresos y calificacion normal.",
                25000,
                15
            ),
            (
                2,
                "Pequeña Empresa (Banca Negocios)",
                "RUC activo, ventas anuales < 5M soles, max 2 representantes legales.",
                150000,
                12
            ),
            (
                3,
                "Clientes Comerciales (Corporate)",
                "Estructuras complejas, requiere Escritura Publica, poderes Sunarp y EEFF auditados.",
                2000000,
                8
            )
        ]

        # Ajustamos el VALUES para recibir el bloque optimizado (%s sin parentesis)
        query = f"""
        INSERT INTO {schema}.tipocliente
        (
            id_tipo_cliente,
            nombre_tipo,
            descripcion,
            monto_maximo_prestamo,
            tasa_interes_base
        )
        VALUES %s
        ON CONFLICT (id_tipo_cliente)
        DO NOTHING;
        """

        # ELIMINAMOS EL BUCLE FOR: Ahora se envía toda la matriz de datos en un solo viaje
        execute_values(cursor, query, datos)

        connection.commit()
        print("¡TipoCliente generado correctamente con los 3 segmentos oficiales!")

    except psycopg2.Error as error:
        print("ERROR:", error)
        if connection:
            connection.rollback()

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    generar_tipo_cliente("public")