import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__))))
load_dotenv()

conn_str = os.getenv("DATABASE_URL")

try:
    print(f"Connecting to: {conn_str}")
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    # Dropear dependencias que puedan interrumpir la re-creación de tablas (Vistas y Triggers del script original)
    print("Dropping legacy views...")
    cur.execute("DROP VIEW IF EXISTS v_resumen_mensual, v_prestamos_activos, v_gastos_mes_actual CASCADE;")
    
    print("Dropping legacy tables to let Alembic recreate them cleanly...")
    cur.execute("DROP TABLE IF EXISTS transacciones, prestamos, presupuestos, metas_ahorro, categorias, cuentas, usuarios CASCADE;")
    
    cur.execute("DROP TYPE IF EXISTS tipo_transaccion, tipo_cuenta, estado_prestamo, tipo_prestamo CASCADE;")
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database cleaned up successfully. Ready for Alembic.")
except Exception as e:
    print(f"Error cleaning DB: {e}")
