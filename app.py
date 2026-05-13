from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os

app = Flask(__name__)
app.secret_key = 'maryori123'
CORS(app)

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='comunidad_agro',
        user='postgres',
        password='maryori123',  
        port=5432
    )

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# ------------------ REGISTRO DE USUARIO ------------------
@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.json
    print("Datos recibidos:", data)
    
    # Validar campos obligatorios
    campos_requeridos = ['dpi', 'primerNombre', 'primerApellido', 'telefono', 'email', 'contrasena', 'rol']
    for campo in campos_requeridos:
        if campo not in data or not data[campo]:
            return jsonify({'error': f'Falta el campo: {campo}'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Obtener ID del tipo de usuario
        cur.execute("SELECT idtipousuario FROM tipousuario WHERE descripciontipousuario = %s", (data['rol'],))
        tipo = cur.fetchone()
        print(f"Tipo usuario encontrado: {tipo}")
        
        if not tipo:
            return jsonify({'error': f'Rol inválido: {data["rol"]}'}), 400
        
        tipo_id = tipo[0]
        
        # 2. Obtener ID del estado activo
        cur.execute("SELECT idestado FROM estadousuario WHERE descripcionestadousuario = 'activo'")
        estado = cur.fetchone()
        print(f"Estado encontrado: {estado}")
        
        if not estado:
            return jsonify({'error': 'Estado "activo" no encontrado'}), 400
        
        estado_id = estado[0]
        
        # 3. Encriptar contraseña
        hashed = bcrypt.hashpw(data['contrasena'].encode('utf-8'), bcrypt.gensalt())
        
        # 4. Insertar usuario
        cur.execute("""
            INSERT INTO usuario (
                dpiusuario, 
                primernombre, 
                segundonombre, 
                primerapellido, 
                segundoapellido, 
                telefonousuario, 
                email, 
                contrasena, 
                tipousuario, 
                idestadousuario
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING idusuario
        """, (
            data['dpi'], 
            data['primerNombre'], 
            data.get('segundoNombre'), 
            data['primerApellido'], 
            data.get('segundoApellido'), 
            data['telefono'], 
            data['email'], 
            hashed.decode('utf-8'), 
            tipo_id, 
            estado_id
        ))
        
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"Usuario registrado con ID: {nuevo_id}")
        return jsonify({'mensaje': 'Usuario registrado exitosamente', 'id': nuevo_id}), 201
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        error_msg = str(e)
        print(f"Error de integridad: {error_msg}")
        if 'email' in error_msg.lower():
            return jsonify({'error': 'El email ya está registrado'}), 400
        elif 'dpi' in error_msg.lower():
            return jsonify({'error': 'El DPI ya está registrado'}), 400
        return jsonify({'error': f'Error: {error_msg}'}), 400
    except Exception as e:
        conn.rollback()
        print(f"Error inesperado: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

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
    cur.close()
    conn.close()
    
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 401
    
    # user[0]=id, user[1]=nombre, user[2]=apellido, user[3]=contrasena, user[4]=rol, user[5]=estado
    if user[5] != 1:  # 1 = activo
        return jsonify({'error': 'Usuario bloqueado o suspendido'}), 403
    
    if bcrypt.checkpw(contrasena.encode('utf-8'), user[3].encode('utf-8')):
        session['usuario_id'] = user[0]
        session['rol'] = user[4]
        session['nombre'] = f"{user[1]} {user[2]}"
        
        # Obtener el nombre del rol
        cur2 = get_db_connection()
        cur2cursor = cur2.cursor()
        cur2cursor.execute("SELECT descripciontipousuario FROM tipousuario WHERE idtipousuario = %s", (user[4],))
        rol_nombre = cur2cursor.fetchone()
        cur2cursor.close()
        cur2.close()
        
        return jsonify({
            'id': user[0],
            'nombre': session['nombre'],
            'rol': rol_nombre[0] if rol_nombre else user[4],
            'mensaje': 'Sesión iniciada'
        })
    else:
        return jsonify({'error': 'Contraseña incorrecta'}), 401
    
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'mensaje': 'Sesión cerrada'})

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
    
    # Convertir a lista de diccionarios
    resultado = []
    for p in productos:
        resultado.append({
            'idproducto': p[0],
            'nombreproducto': p[1],
            'descripcion': p[2],
            'precio': float(p[3]),
            'cantidad_disponible': float(p[4]) if p[4] else 0,
            'unidad': p[5],
            'productor_nombre': p[6],
            'idproductor': p[7]
        })
    
    return jsonify(resultado)

@app.route('/api/mis-productos', methods=['GET'])
def mis_productos():
    if 'usuario_id' not in session or session['rol'] != 'productor':
        return jsonify({'error': 'No autorizado'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM productos WHERE productor_id = %s AND activo = TRUE", (session['usuario_id'],))
    productos = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(productos)

# ==================== CREAR PRODUCTO (con unidad de medida) ====================
@app.route('/api/productos', methods=['POST'])
def crear_producto():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión'}), 401
    
    # Verificar que sea productor
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT tipousuario FROM usuario WHERE idusuario = %s", (session['usuario_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user or user[0] != 1:  # 1 = productor
        return jsonify({'error': 'Solo los productores pueden crear productos'}), 403
    
    data = request.json
    print("Nuevo producto:", data)
    
    # Validar campos
    if not data.get('nombre') or not data.get('precio') or not data.get('cantidad'):
        return jsonify({'error': 'Faltan campos: nombre, precio, cantidad'}), 400
    
    # Obtener ID de unidad de medida
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT idunidad FROM unidadmedida WHERE abreviatura = %s OR nombreunidad = %s", 
                (data.get('unidad', 'kg'), data.get('unidad', 'kg')))
    unidad = cur.fetchone()
    
    unidad_id = unidad[0] if unidad else 1  # 1 = kg por defecto
    
    # Insertar producto
    cur.execute("""
        INSERT INTO producto (nombreproducto, descripcion, precio, idunidadmedida, idproductor, cantidaddisponible)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING idproducto
    """, (data['nombre'], data.get('descripcion', ''), data['precio'], unidad_id, session['usuario_id'], data['cantidad']))
    
    nuevo_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'mensaje': 'Producto registrado', 'id': nuevo_id}), 201

@app.route('/api/productos/<int:producto_id>', methods=['PUT'])
def actualizar_producto(producto_id):
    if 'usuario_id' not in session or session['rol'] != 'productor':
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE productos 
        SET precio = %s, cantidad_disponible = %s, nombre = %s, descripcion = %s
        WHERE id = %s AND productor_id = %s
    """, (data['precio'], data['cantidad'], data['nombre'], data.get('descripcion', ''), producto_id, session['usuario_id']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensaje': 'Producto actualizado'})

# ------------------ PEDIDOS ------------------
@app.route('/api/pedidos', methods=['POST'])
def crear_pedido():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión'}), 401
    
    data = request.json
    producto_id = data.get('producto_id')
    cantidad = data.get('cantidad')
    
    if not producto_id or not cantidad:
        return jsonify({'error': 'Faltan producto_id o cantidad'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Obtener producto y su productor
    cur.execute("""
        SELECT p.idproductor, p.precio, p.cantidaddisponible, p.nombreproducto
        FROM producto p
        WHERE p.idproducto = %s AND p.activo = true
    """, (producto_id,))
    producto = cur.fetchone()
    
    if not producto:
        cur.close()
        conn.close()
        return jsonify({'error': 'Producto no disponible'}), 404
    
    productor_id = producto[0]
    precio = producto[1]
    disponible = producto[2]
    
    if cantidad > disponible:
        cur.close()
        conn.close()
        return jsonify({'error': f'Solo hay {disponible} disponibles'}), 400
    
    # Obtener estado pendiente (id = 1 generalmente)
    cur.execute("SELECT idestadopedido FROM estadopedido WHERE descripcionestadopedido = 'pendiente'")
    estado = cur.fetchone()
    estado_id = estado[0] if estado else 1
    
    # Crear pedido
    cur.execute("""
        INSERT INTO pedido (idcliente, idproductor, idestadopedido)
        VALUES (%s, %s, %s)
        RETURNING idpedido
    """, (session['usuario_id'], productor_id, estado_id))
    
    pedido_id = cur.fetchone()[0]
    
    # Crear producto_pedido
    cur.execute("""
        INSERT INTO productopedido (idpedido, idproducto, cantidad, preciounitario)
        VALUES (%s, %s, %s, %s)
    """, (pedido_id, producto_id, cantidad, precio))
    
    # Registrar en historial
    cur.execute("""
        INSERT INTO historialpedido (idpedido, estadohistorialpedido, comentario)
        VALUES (%s, 'pendiente', 'Pedido creado por cliente')
    """, (pedido_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'mensaje': 'Pedido creado', 'pedido_id': pedido_id}), 201

@app.route('/api/mis-pedidos', methods=['GET'])
def mis_pedidos():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesión'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ver el rol del usuario
    cur.execute("SELECT tipousuario FROM usuario WHERE idusuario = %s", (session['usuario_id'],))
    user = cur.fetchone()
    rol_id = user[0] if user else None
    
    if rol_id == 2:  # Comprador
        cur.execute("""
            SELECT p.idpedido, prod.nombreproducto, pp.cantidad, pp.preciounitario,
                   p.idestadopedido, ep.descripcionestadopedido,
                   u.primernombre || ' ' || u.primerapellido as productor_nombre
            FROM pedido p
            JOIN productopedido pp ON p.idpedido = pp.idpedido
            JOIN producto prod ON pp.idproducto = prod.idproducto
            JOIN estadopedido ep ON p.idestadopedido = ep.idestadopedido
            JOIN usuario u ON p.idproductor = u.idusuario
            WHERE p.idcliente = %s
            ORDER BY p.fechasolicitud DESC
        """, (session['usuario_id'],))
    else:  # Productor o admin
        cur.execute("""
            SELECT p.idpedido, prod.nombreproducto, pp.cantidad, pp.preciounitario,
                   p.idestadopedido, ep.descripcionestadopedido,
                   u.primernombre || ' ' || u.primerapellido as comprador_nombre
            FROM pedido p
            JOIN productopedido pp ON p.idpedido = pp.idpedido
            JOIN producto prod ON pp.idproducto = prod.idproducto
            JOIN estadopedido ep ON p.idestadopedido = ep.idestadopedido
            JOIN usuario u ON p.idcliente = u.idusuario
            WHERE p.idproductor = %s
            ORDER BY p.fechasolicitud DESC
        """, (session['usuario_id'],))
    
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    
    resultado = []
    for p in pedidos:
        resultado.append({
            'idpedido': p[0],
            'producto_nombre': p[1],
            'cantidad': float(p[2]),
            'precio': float(p[3]),
            'estado_id': p[4],
            'estado': p[5],
            'contraparte_nombre': p[6]
        })
    
    return jsonify(resultado)

@app.route('/api/pedidos/<int:pedido_id>/gestionar', methods=['PUT'])
def gestionar_pedido(pedido_id):
    if 'usuario_id' not in session or session['rol'] != 'productor':
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.json
    nuevo_estado = data.get('estado')  # 'aceptado' o 'rechazado'
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if nuevo_estado == 'aceptado':
        # Verificar disponibilidad
        cur.execute("""
            SELECT p.cantidad_solicitada, pr.cantidad_disponible 
            FROM pedidos p
            JOIN productos pr ON p.producto_id = pr.id
            WHERE p.id = %s AND p.productor_id = %s
        """, (pedido_id, session['usuario_id']))
        pedido = cur.fetchone()
        if pedido and pedido['cantidad_solicitada'] > pedido['cantidad_disponible']:
            return jsonify({'error': 'Ya no hay suficiente stock'}), 400
        # Restar stock
        cur.execute("""
            UPDATE productos 
            SET cantidad_disponible = cantidad_disponible - (
                SELECT cantidad_solicitada FROM pedidos WHERE id = %s
            )
            WHERE id = (SELECT producto_id FROM pedidos WHERE id = %s)
        """, (pedido_id, pedido_id))
    
    cur.execute("""
        UPDATE pedidos SET estado = %s 
        WHERE id = %s AND productor_id = %s
    """, (nuevo_estado, pedido_id, session['usuario_id']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensaje': f'Pedido {nuevo_estado}'})

@app.route('/api/pedidos/<int:pedido_id>/confirmar-entrega', methods=['POST'])
def confirmar_entrega(pedido_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesión'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM pedidos WHERE id = %s", (pedido_id,))
    pedido = cur.fetchone()
    if not pedido:
        return jsonify({'error': 'Pedido no encontrado'}), 404
    
    if pedido['estado'] != 'aceptado':
        return jsonify({'error': 'El pedido debe estar aceptado primero'}), 400
    
    if session['usuario_id'] == pedido['comprador_id']:
        cur.execute("UPDATE pedidos SET confirmacion_comprador = TRUE WHERE id = %s", (pedido_id,))
    elif session['usuario_id'] == pedido['productor_id']:
        cur.execute("UPDATE pedidos SET confirmacion_productor = TRUE WHERE id = %s", (pedido_id,))
    else:
        return jsonify({'error': 'No eres parte del pedido'}), 403
    
    cur.execute("SELECT confirmacion_comprador, confirmacion_productor FROM pedidos WHERE id = %s", (pedido_id,))
    actualizado = cur.fetchone()
    if actualizado['confirmacion_comprador'] and actualizado['confirmacion_productor']:
        cur.execute("UPDATE pedidos SET estado = 'completado' WHERE id = %s", (pedido_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensaje': 'Entrega confirmada'})

# ------------------ CALIFICACIONES ------------------
@app.route('/api/calificar', methods=['POST'])
def calificar():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesión'}), 401
    
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verificar que el pedido esté completado
    cur.execute("SELECT estado FROM pedidos WHERE id = %s", (data['pedido_id'],))
    pedido = cur.fetchone()
    if not pedido or pedido['estado'] != 'completado':
        return jsonify({'error': 'Solo se puede calificar después de completar la entrega'}), 400
    
    cur.execute("""
        INSERT INTO calificaciones (calificador_id, calificado_id, pedido_id, puntuacion, comentario)
        VALUES (%s, %s, %s, %s, %s)
    """, (session['usuario_id'], data['calificado_id'], data['pedido_id'], data['puntuacion'], data.get('comentario', '')))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensaje': 'Calificación registrada'}), 201

@app.route('/api/calificaciones/<int:usuario_id>', methods=['GET'])
def obtener_calificaciones(usuario_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(puntuacion) as promedio, COUNT(*) as total
        FROM calificaciones
        WHERE calificado_id = %s
    """, (usuario_id,))
    resultado = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify(resultado or {'promedio': 0, 'total': 0})

# ------------------ ADMIN ------------------
@app.route('/api/admin/reportes', methods=['GET'])
def ver_reportes():
    if 'usuario_id' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'Solo administradores'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, u1.nombre_completo as reportante_nombre, u2.nombre_completo as reportado_nombre
        FROM reportes r
        JOIN usuarios u1 ON r.usuario_reportante = u1.id
        JOIN usuarios u2 ON r.usuario_reportado = u2.id
        WHERE r.estado = 'pendiente'
        ORDER BY r.fecha_reporte DESC
    """)
    reportes = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(reportes)

@app.route('/api/admin/reportar', methods=['POST'])
def reportar_usuario():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesión'}), 401
    
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reportes (usuario_reportante, usuario_reportado, motivo)
        VALUES (%s, %s, %s)
    """, (session['usuario_id'], data['usuario_reportado'], data['motivo']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensaje': 'Reporte enviado a la asociación'}), 201

@app.route('/api/admin/bloquear/<int:usuario_id>', methods=['PUT'])
def bloquear_usuario(usuario_id):
    if 'usuario_id' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'Solo administradores'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET estado = 'bloqueado' WHERE id = %s", (usuario_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensaje': 'Usuario bloqueado'})

@app.route('/api/estadisticas', methods=['GET'])
def estadisticas():
    if 'usuario_id' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COUNT(DISTINCT p.id) as total_pedidos,
            COUNT(DISTINCT u.id) as total_usuarios,
            COUNT(DISTINCT pr.id) as total_productos,
            SUM(CASE WHEN p.estado = 'completado' THEN 1 ELSE 0 END) as ventas_completadas
        FROM usuarios u
        LEFT JOIN pedidos p ON 1=1
        LEFT JOIN productos pr ON 1=1
    """)
    stats = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)