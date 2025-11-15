import mysql.connector

DB_CONFIG = {
    'host': '135.181.212.169',
    'port': 3369,
    'user': 'sqlworkerSMP',
    'password': 'SQLdb2024!',
    'database': 'asmp_config'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM instances')
print(f'Total instances: {cursor.fetchone()[0]}')

cursor.execute('SELECT server_name, COUNT(*) FROM instances GROUP BY server_name')
print('\nBy server:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

cursor.execute('SELECT instance_id, instance_name, server_name, port FROM instances ORDER BY server_name, port')
print('\nAll instances:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} ({row[2]}:{row[3]})')

cursor.close()
conn.close()
