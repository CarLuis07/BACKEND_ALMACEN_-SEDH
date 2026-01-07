import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="almacen_db",
    user="postgres",
    password="Admin123"
)

cur = conn.cursor()

# Buscar tablas con "programa" en el nombre
cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_name LIKE '%programa%' 
    ORDER BY table_schema, table_name;
""")

tablas = cur.fetchall()
print("=== TABLAS CON 'programa' EN EL NOMBRE ===")
for schema, tabla in tablas:
    print(f"  {schema}.{tabla}")

# Ver la estructura de la tabla requisiciones
print("\n=== COLUMNAS DE requisiciones.requisiciones ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'requisiciones' 
    AND table_name = 'requisiciones'
    AND column_name LIKE '%programa%'
    ORDER BY ordinal_position;
""")

columnas = cur.fetchall()
for col, tipo in columnas:
    print(f"  {col} ({tipo})")

cur.close()
conn.close()
