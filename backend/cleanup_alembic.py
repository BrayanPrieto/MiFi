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
    
    cur.execute("DROP TABLE IF EXISTS alembic_version CASCADE;")
    cur.execute("DROP INDEX IF EXISTS idx_transacciones_categoria CASCADE;")
    cur.execute("DROP INDEX IF EXISTS idx_transacciones_cuenta CASCADE;")
    cur.execute("DROP INDEX IF EXISTS idx_transacciones_usuario_fecha CASCADE;")
    cur.execute("DROP INDEX IF EXISTS idx_transacciones_usuario_tipo CASCADE;")
    cur.execute("DROP INDEX IF EXISTS idx_transacciones_mes_anio CASCADE;")
    cur.execute("DROP INDEX IF EXISTS idx_prestamos_usuario_estado CASCADE;")
    cur.execute("DROP INDEX IF EXISTS idx_categorias_usuario_tipo CASCADE;")
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database alembic version cleaned up.")
except Exception as e:
    print(f"Error cleaning DB: {e}")
