from app.utils.encoding import force_utf8_output

force_utf8_output()

from app.db import get_connection

conn = get_connection()
print("✅ Connected successfully:", conn)
conn.close()