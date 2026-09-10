from app.db import get_connection

conn = get_connection()
print("✅ Connected successfully:", conn)
conn.close()