from database.db_vps import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT DATABASE() AS db_name")
row = cursor.fetchone()
print(row)
conn.close()