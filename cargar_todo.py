# Importar todas las funciones de tus scripts
from poblar_maestras import cargar_tablas_maestras
from poblar_persona import generar_e_insertar_personas
from poblar_cliente import generar_e_insertar_clientes
from poblar_asesor import generar_e_insertar_asesores
from poblar_aval import generar_e_insertar_avales
from poblar_cuenta_bancaria import generar_e_insertar_cuentas
from poblar_solicitud import generar_e_insertar_solicitudes
from poblar_evaluacion import generar_e_insertar_evaluaciones
from poblar_prestamo import generar_e_insertar_prestamos
from poblar_ciclo_pagos import procesar_ciclo_pagos_y_desembolsos
from poblar_retorno import poblar_fase_retorno


def ejecutar_carga_masiva():
    # ========================================================
    # 1. CONFIGURA TU VOLUMEN DE DATOS AQUÍ
    # ========================================================
    VOLUMEN_DATOS = 10000  # <--- Cambia esto a 10000
    SCHEMA = "public"

    print(f"--- INICIANDO CARGA MASIVA DE {VOLUMEN_DATOS} REGISTROS ---")

    # 1. Tablas Maestras (No dependen de cantidad, son catálogos fijos)
    cargar_tablas_maestras(schema=SCHEMA)

    # 2. Base Poblacional (Aquí nacen los 10,000 registros)
    # Le sumamos unos 500 extra a personas para que haya "sobrantes" para asesores y avales
    generar_e_insertar_personas(VOLUMEN_DATOS + 500, schema=SCHEMA)

    # 3. Entidades Principales
    generar_e_insertar_clientes(VOLUMEN_DATOS, schema=SCHEMA)
    generar_e_insertar_asesores(100, schema=SCHEMA)  # Con 100 asesores basta para un banco simulado
    generar_e_insertar_avales(200, schema=SCHEMA)  # 200 avales aleatorios

    # 4. Productos Pasivos (Cuentas)
    # Este script no recibe número porque procesa a TODOS los clientes que encuentre
    generar_e_insertar_cuentas(schema=SCHEMA)

    # 5. Pipeline de Créditos (Préstamos)
    # Le decimos que genere solicitudes para gran parte de esos 10,000 clientes
    generar_e_insertar_solicitudes(int(VOLUMEN_DATOS * 0.8), schema=SCHEMA)  # El 80% pedirá préstamo
    generar_e_insertar_evaluaciones(schema=SCHEMA)
    generar_e_insertar_prestamos(schema=SCHEMA)

    # 6. Transaccionalidad
    procesar_ciclo_pagos_y_desembolsos(schema=SCHEMA)

    poblar_fase_retorno()

    print("======================================================")
    print("🚀 ¡CARGA MASIVA FINALIZADA CON ÉXITO! 🚀")
    print("======================================================")


if __name__ == "__main__":
    ejecutar_carga_masiva()