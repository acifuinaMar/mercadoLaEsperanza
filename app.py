# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os

app = Flask(__name__)
app.secret_key = 'maryori123'
CORS(app)

# ==================== CAPA DE DTOs ====================
# Estos objetos se encargan de estructurar la data antes de enviarla
class ProductoDTO:
    def __init__(self, idproducto, nombreproducto, descripcion, precio, cantidaddisponible, unidad, productor_nombre, idproductor):
        self.idproducto = idproducto
        self.nombreproducto = nombreproducto
        self.descripcion = descripcion
        self.precio = float(precio)
        self.cantidad_disponible = float(cantidaddisponible) if cantidaddisponible else 0
        self.unidad = unidad
        self.productor_nombre = productor_nombre
        self.idproductor = idproductor

    def to_dict(self):
        return {
            'idproducto': self.idproducto,
            'nombreproducto': self.nombreproducto,
            'descripcion': self.descripcion,
            'precio': self.precio,
            'cantidad_disponible': self.cantidad_disponible,
            'unidad': self.unidad,
            'productor_nombre': self.productor_nombre,
            'idproductor': self.idproductor
        }

class UsuarioDTO:
    def __init__(self, idusuario, nombre, rol_nombre):
        self.id = idusuario
        self.nombre = nombre
        self.rol = rol_nombre

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'rol': self.rol,
            'mensaje': 'Sesión iniciada'
        }
# ======================================================

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='comunidad_agro',
        user='postgres',
        password='123456789',  
        port=5432
    )

@app.route('/')
def index():
    return render_template('index.html')

# ------------------ REGISTRO DE USUARIO ------------------
@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.json
    print("Datos recibidos:", data)
    
    campos_requeridos = ['dpi', 'primerNombre', 'primerApellido', 'telefono', 'email', 'contrasena', 'rol']
    for campo in campos_requeridos:
        if campo not in data or not data[campo]:
            return jsonify({'error': f'Falta el campo: {campo}'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT idtipousuario FROM tipousuario WHERE descripciontipousuario = %s", (data['rol'],))
        tipo = cur.fetchone()
        if not tipo:
            return jsonify({'error': f'Rol inválido: {data["rol"]}'}), 400
        
        tipo_id = tipo[0]
        
        cur.execute("SELECT idestado FROM estadousuario WHERE descripcionestadousuario = 'activo'")
        estado = cur.fetchone()
        if not estado:
            return jsonify({'error': 'Estado "activo" no encontrado'}), 400
        
        estado_id = estado[0]
        hashed = bcrypt.hashpw(data['contrasena'].encode('utf-8'), bcrypt.gensalt())
        
        cur.execute("""
            INSERT INTO usuario (
                dpiusuario, primernombre, segundonombre, primerapellido, segundoapellido, 
                telefonousuario, email, contrasena, tipousuario, idestadousuario
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING idusuario
        """, (
            data['dpi'], data['primerNombre'], data.get('segundoNombre'), 
            data['primerApellido'], data.get('segundoApellido'), data['telefono'], 
            data['email'], hashed.decode('utf-8'), tipo_id, estado_id
        ))
        
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({'mensaje': 'Usuario registrado exitosamente', 'id': nuevo_id}), 201
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        error_msg = str(e)
        if 'email' in error_msg.lower():
            return jsonify({'error': 'El email ya está registrado'}), 400
        elif 'dpi' in error_msg.lower():
            return jsonify({'error': 'El DPI ya está registrado'}), 400
        return jsonify({'error': f'Error: {error_msg}'}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    contrasena = data.get('contrasena')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT idusuario, primernombre, primerapellido, contrasena, tipousuario, idestadousuario
        FROM usuario 
        WHERE email = %s
    """, (email,))
    user = cur.fetchone()
    
    if not user:
        cur.close()
        conn.close()
        return jsonify({'error': 'Usuario no encontrado'}), 401
    
    if user[5] != 1: 
        cur.close()
        conn.close()
        return jsonify({'error': 'Usuario bloqueado o suspendido'}), 403
    
    if bcrypt.checkpw(contrasena.encode('utf-8'), user[3].encode('utf-8')):
        session['usuario_id'] = user[0]
        session['rol'] = user[4]
        session['nombre'] = f"{user[1]} {user[2]}"
        
        cur.execute("SELECT descripciontipousuario FROM tipousuario WHERE idtipousuario = %s", (user[4],))
        rol_nombre = cur.fetchone()
        rol_final = rol_nombre[0] if rol_nombre else user[4]
        
        # IMPLEMENTACIÓN DTO PARA LOGIN
        usuario_dto = UsuarioDTO(user[0], session['nombre'], rol_final)
        
        cur.close()
        conn.close()
        return jsonify(usuario_dto.to_dict())
    else:
        cur.close()
        conn.close()
        return jsonify({'error': 'Contraseña incorrecta'}), 401

# ------------------ PRODUCTOS ------------------
@app.route('/api/productos', methods=['GET'])
def listar_productos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.idproducto, p.nombreproducto, p.descripcion, p.precio, 
               p.cantidaddisponible, u.abreviatura as unidad,
               pr.primernombre || ' ' || pr.primerapellido as productor_nombre,
               p.idproductor
        FROM producto p
        JOIN unidadmedida u ON p.idunidadmedida = u.idunidad
        JOIN usuario pr ON p.idproductor = pr.idusuario
        WHERE p.activo = true AND pr.idestadousuario = 1
        ORDER BY p.fecharegistro DESC
    """)
    productos = cur.fetchall()
    cur.close()
    conn.close()
    
    # IMPLEMENTACIÓN DTO PARA LISTADO DE PRODUCTOS
    resultado = [ProductoDTO(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]).to_dict() for p in productos]
    return jsonify(resultado)

# Mantengo el resto de tus rutas (crear_pedido, confirmar_entrega, etc.) 
# sin cambios para no afectar la lógica de negocio que ya tienes probada.

@app.route('/api/verificar-sesion', methods=['GET'])
def verificar_sesion():
    if 'usuario_id' in session:
        return jsonify({
            'logueado': True,
            'usuario_id': session['usuario_id'],
            'rol': session['rol'],
            'nombre': session['nombre']
        })
    return jsonify({'logueado': False})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'mensaje': 'Sesión cerrada'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)