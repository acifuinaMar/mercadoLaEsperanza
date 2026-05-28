import bcrypt
import psycopg2

# Conectar a la BD
conn = psycopg2.connect(
    host='localhost',
    database='comunidad_agro',
    user='postgres',
    password='maryori123',
    port=5432
)
cur = conn.cursor()

# Contraseña en texto plano
contrasena = 'admin123'
hashed = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt())

# Crear nuevo admin
try:
    cur.execute("""
        INSERT INTO usuario (
            dpiusuario, primernombre, primerapellido, telefonousuario, 
            email, contrasena, tipousuario, idestadousuario
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        '9999999999999',
        'Admin',
        'Sistema',
        '00000000',
        'admin2@comunidad.com',
        hashed.decode('utf-8'),
        3,
        1
    ))
    
    conn.commit()
    print("Nuevo admin creado exitosamente")
    print("Email: admin2@comunidad.com")
    print("Contraseña: admin123")
    
except psycopg2.IntegrityError as e:
    conn.rollback()
    if 'email' in str(e):
        print("Error: Ese email ya existe, prueba con otro")
    else:
        print(f"Error: {e}")
finally:
    cur.close()
    conn.close()