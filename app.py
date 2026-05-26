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
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'comunidad_agro'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'maryori123'),
        port=os.environ.get('DB_PORT', 5432)
    )

# ==================== DTOs ====================

class UsuarioDTO:
    def __init__(self, dpi, primer_nombre, segundo_nombre, primer_apellido, 
                 segundo_apellido, telefono, email, contrasena, rol):
        self.dpi = dpi
        self.primer_nombre = primer_nombre
        self.segundo_nombre = segundo_nombre
        self.primer_apellido = primer_apellido
        self.segundo_apellido = segundo_apellido
        self.telefono = telefono
        self.email = email
        self.contrasena = contrasena
        self.rol = rol
    
    @classmethod
    def from_json(cls, data):
        return cls(
            dpi=data.get('dpi'),
            primer_nombre=data.get('primerNombre'),
            segundo_nombre=data.get('segundoNombre'),
            primer_apellido=data.get('primerApellido'),
            segundo_apellido=data.get('segundoApellido'),
            telefono=data.get('telefono'),
            email=data.get('email'),
            contrasena=data.get('contrasena'),
            rol=data.get('rol')
        )
    
    def validar(self):
        campos = [self.dpi, self.primer_nombre, self.primer_apellido, 
                  self.telefono, self.email, self.contrasena, self.rol]
        return all(campos)

class ProductoDTO:
    def __init__(self, nombre, descripcion, precio, cantidad, unidad='kg'):
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.cantidad = cantidad
        self.unidad = unidad
    
    @classmethod
    def from_json(cls, data):
        return cls(
            nombre=data.get('nombre'),
            descripcion=data.get('descripcion', ''),
            precio=data.get('precio'),
            cantidad=data.get('cantidad'),
            unidad=data.get('unidad', 'kg')
        )
    
    def validar(self):
        return all([self.nombre, self.precio, self.cantidad])

class PedidoDTO:
    def __init__(self, producto_id, cantidad):
        self.producto_id = producto_id
        self.cantidad = cantidad
    
    @classmethod
    def from_json(cls, data):
        return cls(
            producto_id=data.get('producto_id'),
            cantidad=data.get('cantidad')
        )
    
    def validar(self):
        return all([self.producto_id, self.cantidad])

class CalificacionDTO:
    def __init__(self, pedido_id, calificado_id, puntuacion, comentario=''):
        self.pedido_id = pedido_id
        self.calificado_id = calificado_id
        self.puntuacion = puntuacion
        self.comentario = comentario
    
    @classmethod
    def from_json(cls, data):
        return cls(
            pedido_id=data.get('pedido_id'),
            calificado_id=data.get('calificado_id'),
            puntuacion=data.get('puntuacion'),
            comentario=data.get('comentario', '')
        )
    
    def validar(self):
        return all([self.pedido_id, self.calificado_id, self.puntuacion])

class ReporteDTO:
    def __init__(self, usuario_reportado, motivo):
        self.usuario_reportado = usuario_reportado
        self.motivo = motivo
    
    @classmethod
    def from_json(cls, data):
        return cls(
            usuario_reportado=data.get('usuario_reportado'),
            motivo=data.get('motivo')
        )
    
    def validar(self):
        return all([self.usuario_reportado, self.motivo])

# ==================== RUTAS ====================

@app.route('/')
def index():
    return render_template('index.html')

# ------------------ AUTENTICACION ------------------

@app.route('/api/registro', methods=['POST'])
def registro():
    try:
        usuario = UsuarioDTO.from_json(request.json)
        print(f"Datos recibidos: {usuario.__dict__}")
        
        if not usuario.validar():
            return jsonify({'error': 'Faltan campos obligatorios'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Obtener ID del tipo de usuario
        cur.execute("SELECT idtipousuario FROM tipousuario WHERE descripciontipousuario = %s", (usuario.rol,))
        tipo = cur.fetchone()
        if not tipo:
            return jsonify({'error': f'Rol inválido: {usuario.rol}'}), 400
        tipo_id = tipo[0]
        
        # Obtener ID del estado activo
        cur.execute("SELECT idestado FROM estadousuario WHERE descripcionestadousuario = 'activo'")
        estado = cur.fetchone()
        if not estado:
            return jsonify({'error': 'Estado "activo" no encontrado'}), 400
        estado_id = estado[0]
        
        # Encriptar contraseña
        hashed = bcrypt.hashpw(usuario.contrasena.encode('utf-8'), bcrypt.gensalt())
        
        # Insertar usuario
        cur.execute("""
            INSERT INTO usuario (
                dpiusuario, primernombre, segundonombre, primerapellido, 
                segundoapellido, telefonousuario, email, contrasena, 
                tipousuario, idestadousuario
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING idusuario
        """, (
            usuario.dpi, usuario.primer_nombre, usuario.segundo_nombre, 
            usuario.primer_apellido, usuario.segundo_apellido, 
            usuario.telefono, usuario.email, hashed.decode('utf-8'), 
            tipo_id, estado_id
        ))
        
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"Usuario registrado con ID: {nuevo_id}")
        return jsonify({'mensaje': 'Usuario registrado exitosamente', 'id': nuevo_id}), 201
        
    except psycopg2.IntegrityError as e:
        if 'conn' in locals():
            conn.rollback()
        error_msg = str(e)
        if 'email' in error_msg.lower():
            return jsonify({'error': 'El email ya está registrado'}), 400
        elif 'dpi' in error_msg.lower():
            return jsonify({'error': 'El DPI ya está registrado'}), 400
        return jsonify({'error': f'Error: {error_msg}'}), 400
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error inesperado: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
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
    
    # user[0]=id, user[1]=nombre, user[2]=apellido, user[3]=contrasena, user[4]=rol_id, user[5]=estado
    if user[5] != 1:  # 1 = activo
        return jsonify({'error': 'Usuario bloqueado o suspendido'}), 403
    
    if bcrypt.checkpw(contrasena.encode('utf-8'), user[3].encode('utf-8')):
        # Convertir rol_id a texto para el frontend
        rol_texto = ''
        if user[4] == 1:
            rol_texto = 'productor'
        elif user[4] == 2:
            rol_texto = 'comprador'
        elif user[4] == 3:
            rol_texto = 'admin'
        else:
            rol_texto = 'comprador'
        
        session['usuario_id'] = user[0]
        session['rol'] = rol_texto  # Guardamos texto, no número
        session['rol_id'] = user[4]  # Guardamos también el número por si acaso
        session['nombre'] = f"{user[1]} {user[2]}"
        
        return jsonify({
            'id': user[0],
            'nombre': session['nombre'],
            'rol': rol_texto,
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
    return jsonify([{'idproducto': p[0], 'nombreproducto': p[1], 'descripcion': p[2], 'precio': float(p[3]), 'cantidad_disponible': float(p[4]) if p[4] else 0, 'unidad': p[5], 'productor_nombre': p[6], 'idproductor': p[7]} for p in productos])

@app.route('/api/mis-productos', methods=['GET'])
def mis_productos():
    if 'usuario_id' not in session or session.get('rol') != 'productor':
        return jsonify({'error': 'No autorizado'}), 401
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT idproducto, nombreproducto, descripcion, precio, cantidaddisponible FROM producto WHERE idproductor = %s AND activo = true", (session['usuario_id'],))
    productos = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{'idproducto': p[0], 'nombreproducto': p[1], 'descripcion': p[2], 'precio': float(p[3]), 'cantidaddisponible': float(p[4])} for p in productos])

@app.route('/api/productos', methods=['POST'])
def crear_producto():
    if 'usuario_id' not in session or session.get('rol') != 'productor':
        return jsonify({'error': 'No autorizado'}), 403
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO producto (nombreproducto, descripcion, precio, idunidadmedida, idproductor, cantidaddisponible, activo) VALUES (%s, %s, %s, %s, %s, %s, true) RETURNING idproducto", 
                    (data['nombre'], data.get('descripcion', ''), data['precio'], 1, session['usuario_id'], data['cantidad']))
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'id': nuevo_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/productos/<int:producto_id>', methods=['DELETE'])
def eliminar_producto(producto_id):
    if 'usuario_id' not in session or session.get('rol') != 'productor':
        return jsonify({'error': 'No autorizado'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Intentamos eliminar el registro
        cur.execute("DELETE FROM producto WHERE idproducto = %s AND idproductor = %s", 
                    (producto_id, session['usuario_id']))
        conn.commit()
        return jsonify({'mensaje': 'Producto eliminado correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    datos = request.get_json()
    try:
        conn = get_db_connection() # Asegúrate de que esta función sea la que usas siempre
        cur = conn.cursor()
        cur.execute("""
            UPDATE productos 
            SET nombreproducto = %s, 
                descripcion = %s, 
                precio = %s, 
                cantidad_disponible = %s 
            WHERE idproducto = %s
        """, (datos['nombre'], datos['descripcion'], datos['precio'], datos['cantidad'], id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"mensaje": "Producto actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ------------------ PEDIDOS ------------------

@app.route('/api/pedidos', methods=['POST'])
def crear_pedido():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión'}), 401
    
    try:
        pedido = PedidoDTO.from_json(request.json)
        
        if not pedido.validar():
            return jsonify({'error': 'Faltan producto_id o cantidad'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT p.idproductor, p.precio, p.cantidaddisponible, p.nombreproducto
            FROM producto p
            WHERE p.idproducto = %s AND p.activo = true
        """, (pedido.producto_id,))
        producto = cur.fetchone()
        
        if not producto:
            cur.close()
            conn.close()
            return jsonify({'error': 'Producto no disponible'}), 404
        
        productor_id = producto[0]
        precio = producto[1]
        disponible = producto[2]
        
        if pedido.cantidad > disponible:
            cur.close()
            conn.close()
            return jsonify({'error': f'Solo hay {disponible} disponibles'}), 400
        
        cur.execute("SELECT idestadopedido FROM estadopedido WHERE descripcionestadopedido = 'pendiente'")
        estado = cur.fetchone()
        estado_id = estado[0] if estado else 1
        
        cur.execute("""
            INSERT INTO pedido (idcliente, idproductor, idestadopedido)
            VALUES (%s, %s, %s)
            RETURNING idpedido
        """, (session['usuario_id'], productor_id, estado_id))
        
        pedido_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO productopedido (idpedido, idproducto, cantidad, preciounitario)
            VALUES (%s, %s, %s, %s)
        """, (pedido_id, pedido.producto_id, pedido.cantidad, precio))
        
        cur.execute("""
            INSERT INTO historialpedido (idpedido, estadohistorialpedido, comentario)
            VALUES (%s, 'pendiente', 'Pedido creado por cliente')
        """, (pedido_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'mensaje': 'Pedido creado', 'pedido_id': pedido_id}), 201
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mis-pedidos', methods=['GET'])
def mis_pedidos():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesion'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Obtener el rol del usuario desde la sesion
    rol_usuario = session.get('rol')
    usuario_id = session['usuario_id']
    
    print(f"Usuario ID: {usuario_id}, Rol: {rol_usuario}")  # Para debug
    
    if rol_usuario == 'comprador':
        # Como comprador, quiero ver a los productores
        cur.execute("""
            SELECT 
                p.idpedido, 
                prod.nombreproducto, 
                pp.cantidad, 
                pp.preciounitario,
                p.idestadopedido, 
                ep.descripcionestadopedido,
                COALESCE(u.primernombre || ' ' || u.primerapellido, 'Productor desconocido') as contraparte_nombre,
                u.idusuario as contraparte_id
            FROM pedido p
            JOIN productopedido pp ON p.idpedido = pp.idpedido
            JOIN producto prod ON pp.idproducto = prod.idproducto
            JOIN estadopedido ep ON p.idestadopedido = ep.idestadopedido
            JOIN usuario u ON p.idproductor = u.idusuario
            WHERE p.idcliente = %s
            ORDER BY p.fechasolicitud DESC
        """, (usuario_id,))
    else:
        # Como productor (o admin), quiero ver a los compradores
        cur.execute("""
            SELECT 
                p.idpedido, 
                prod.nombreproducto, 
                pp.cantidad, 
                pp.preciounitario,
                p.idestadopedido, 
                ep.descripcionestadopedido,
                COALESCE(u.primernombre || ' ' || u.primerapellido, 'Comprador desconocido') as contraparte_nombre,
                u.idusuario as contraparte_id
            FROM pedido p
            JOIN productopedido pp ON p.idpedido = pp.idpedido
            JOIN producto prod ON pp.idproducto = prod.idproducto
            JOIN estadopedido ep ON p.idestadopedido = ep.idestadopedido
            JOIN usuario u ON p.idcliente = u.idusuario
            WHERE p.idproductor = %s
            ORDER BY p.fechasolicitud DESC
        """, (usuario_id,))
    
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    
    resultado = []
    for p in pedidos:
        resultado.append({
            'idpedido': p[0],
            'producto_nombre': p[1],
            'cantidad_solicitada': float(p[2]),
            'precio': float(p[3]),
            'estado_id': p[4],
            'estado': p[5],
            'contraparte_nombre': p[6] if p[6] else ('Productor' if rol_usuario == 'comprador' else 'Comprador'),
            'contraparte_id': p[7]
        })
    
    print(f"Pedidos encontrados: {len(resultado)}")  # Para debug
    for r in resultado:
        print(f"  - {r['producto_nombre']} - {r['contraparte_nombre']}")
    
    return jsonify(resultado)

@app.route('/api/pedidos/<int:pedido_id>/gestionar', methods=['PUT'])
def gestionar_pedido(pedido_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión'}), 401
    
    if session.get('rol') != 'productor':
        return jsonify({'error': 'Solo productores pueden gestionar pedidos'}), 403
    
    data = request.json
    nuevo_estado = data.get('estado')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if nuevo_estado == 'aceptado':
        cur.execute("""
            SELECT p.idestadopedido, pr.cantidaddisponible, pp.cantidad
            FROM pedido p
            JOIN productopedido pp ON p.idpedido = pp.idpedido
            JOIN producto pr ON pp.idproducto = pr.idproducto
            WHERE p.idpedido = %s AND p.idproductor = %s
        """, (pedido_id, session['usuario_id']))
        pedido_info = cur.fetchone()
        
        if pedido_info:
            if pedido_info[2] > pedido_info[1]:
                cur.close()
                conn.close()
                return jsonify({'error': 'Ya no hay suficiente stock'}), 400
            
            cur.execute("""
                UPDATE producto 
                SET cantidaddisponible = cantidaddisponible - %s
                WHERE idproducto = (SELECT idproducto FROM productopedido WHERE idpedido = %s)
            """, (pedido_info[2], pedido_id))
    
    # Obtener ID del nuevo estado
    cur.execute("SELECT idestadopedido FROM estadopedido WHERE descripcionestadopedido = %s", (nuevo_estado,))
    estado_id = cur.fetchone()
    
    if estado_id:
        cur.execute("""
            UPDATE pedido SET idestadopedido = %s 
            WHERE idpedido = %s AND idproductor = %s
        """, (estado_id[0], pedido_id, session['usuario_id']))
        
        # Registrar en historial
        cur.execute("""
            INSERT INTO historialpedido (idpedido, estadohistorialpedido, comentario)
            VALUES (%s, %s, 'Productor gestionó el pedido')
        """, (pedido_id, nuevo_estado))
    
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
    
    # Obtener el pedido
    cur.execute("""
        SELECT idcliente, idproductor, idestadopedido 
        FROM pedido 
        WHERE idpedido = %s
    """, (pedido_id,))
    pedido = cur.fetchone()
    
    if not pedido:
        cur.close()
        conn.close()
        return jsonify({'error': 'Pedido no encontrado'}), 404
    
    # Verificar que esté aceptado (idestadopedido = 2 para aceptado)
    if pedido[2] != 2:
        cur.close()
        conn.close()
        return jsonify({'error': 'El pedido debe estar aceptado primero'}), 400
    
    # Verificar si ya existe una entrega
    cur.execute("SELECT * FROM entrega WHERE idpedido = %s", (pedido_id,))
    entrega = cur.fetchone()
    
    if not entrega:
        # Debes incluir idpuntoentrega. 
        # Si no tienes un punto específico, usa un valor por defecto o 
        # asegúrate de obtenerlo del frontend.
        cur.execute("""
            INSERT INTO entrega (idpedido, idestadoentrega, idpuntoentrega)
            VALUES (%s, 1, 1)  -- <-- Cambia el segundo '1' por el ID correcto del punto de entrega
            RETURNING identrega
        """, (pedido_id,))
        identrega = cur.fetchone()[0]
    else:
        identrega = entrega[0]
    
    # Actualizar confirmaciones
    if session['usuario_id'] == pedido[0]:
        cur.execute("UPDATE entrega SET confirmadocliente = true WHERE identrega = %s", (identrega,))
    elif session['usuario_id'] == pedido[1]:
        cur.execute("UPDATE entrega SET confirmadoproductor = true WHERE identrega = %s", (identrega,))
    else:
        cur.close()
        conn.close()
        return jsonify({'error': 'No eres parte del pedido'}), 403
    
    # Verificar si ambas confirmaron
    cur.execute("SELECT confirmadocliente, confirmadoproductor FROM entrega WHERE identrega = %s", (identrega,))
    actualizado = cur.fetchone()
    
    if actualizado[0] and actualizado[1]:
        # Actualizar estado de pedido a completado
        cur.execute("SELECT idestadopedido FROM estadopedido WHERE descripcionestadopedido = 'completado'")
        completado_id = cur.fetchone()
        if completado_id:
            cur.execute("UPDATE pedido SET idestadopedido = %s WHERE idpedido = %s", (completado_id[0], pedido_id))
        
        # Actualizar estado de entrega
        cur.execute("SELECT idestadoentrega FROM estadoentrega WHERE descripcionestadoentrega = 'entregado'")
        entregado_id = cur.fetchone()
        if entregado_id:
            cur.execute("UPDATE entrega SET idestadoentrega = %s WHERE identrega = %s", (entregado_id[0], identrega))
        
        # Registrar en historial
        cur.execute("""
            INSERT INTO historialpedido (idpedido, estadohistorialpedido, comentario)
            VALUES (%s, 'completado', 'Entrega confirmada por ambas partes')
        """, (pedido_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensaje': 'Entrega confirmada'})

# ------------------ CALIFICACIONES ------------------

@app.route('/api/calificar', methods=['POST'])
def calificar():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesión'}), 401
    
    try:
        calificacion = CalificacionDTO.from_json(request.json)
        
        if not calificacion.validar():
            return jsonify({'error': 'Faltan campos: pedido_id, calificado_id, puntuacion'}), 400
        
        if calificacion.puntuacion < 1 or calificacion.puntuacion > 5:
            return jsonify({'error': 'La puntuación debe ser entre 1 y 5'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar que el pedido esté completado
        cur.execute("""
            SELECT p.idestadopedido, ep.descripcionestadopedido
            FROM pedido p
            JOIN estadopedido ep ON p.idestadopedido = ep.idestadopedido
            WHERE p.idpedido = %s
        """, (calificacion.pedido_id,))
        pedido = cur.fetchone()
        
        if not pedido or pedido[1] != 'completado':
            cur.close()
            conn.close()
            return jsonify({'error': 'Solo se puede calificar después de completar la entrega'}), 400
        
        # Verificar que no haya calificado antes
        cur.execute("""
            SELECT * FROM calificacion 
            WHERE idpedido = %s AND idcalificador = %s
        """, (calificacion.pedido_id, session['usuario_id']))
        existe = cur.fetchone()
        
        if existe:
            cur.close()
            conn.close()
            return jsonify({'error': 'Ya calificaste este pedido'}), 400
        
        cur.execute("""
            INSERT INTO calificacion (idcalificador, idcalificado, idpedido, puntaje, comentario)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['usuario_id'], calificacion.calificado_id, 
              calificacion.pedido_id, calificacion.puntuacion, calificacion.comentario))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'mensaje': 'Calificación registrada'}), 201
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/calificaciones/<int:usuario_id>', methods=['GET'])
def obtener_calificaciones(usuario_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(AVG(puntaje), 0) as promedio, COUNT(*) as total
        FROM calificacion
        WHERE idcalificado = %s
    """, (usuario_id,))
    resultado = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify({
        'promedio': float(resultado[0]) if resultado[0] else 0,
        'total': resultado[1] if resultado[1] else 0
    })

# ------------------ ADMIN ------------------

@app.route('/api/admin/reportes', methods=['GET'])
def ver_reportes():
    if 'usuario_id' not in session or session['rol'] != 3:
        return jsonify({'error': 'Solo administradores'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.idreporte, r.comentarioreporte, r.fechaenviorprt, r.estado,
               u1.primernombre || ' ' || u1.primerapellido as reportante_nombre,
               u2.primernombre || ' ' || u2.primerapellido as reportado_nombre,
               r.idemisor, r.idreceptor
        FROM reporte r
        JOIN usuario u1 ON r.idemisor = u1.idusuario
        JOIN usuario u2 ON r.idreceptor = u2.idusuario
        WHERE r.estado = 'pendiente'
        ORDER BY r.fechaenviorprt DESC
    """)
    reportes = cur.fetchall()
    cur.close()
    conn.close()
    
    resultado = []
    for r in reportes:
        resultado.append({
            'idreporte': r[0],
            'motivo': r[1],
            'fecha': r[2],
            'estado': r[3],
            'reportante_nombre': r[4],
            'reportado_nombre': r[5],
            'usuario_reportado': r[7]
        })
    
    return jsonify(resultado)

@app.route('/api/admin/reportar', methods=['POST'])
def reportar_usuario():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesión'}), 401
    
    try:
        reporte = ReporteDTO.from_json(request.json)
        
        if not reporte.validar():
            return jsonify({'error': 'Faltan campos: usuario_reportado, motivo'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reporte (idemisor, idreceptor, comentarioreporte, estado)
            VALUES (%s, %s, %s, 'pendiente')
        """, (session['usuario_id'], reporte.usuario_reportado, reporte.motivo))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'mensaje': 'Reporte enviado a la asociación'}), 201
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/bloquear/<int:usuario_id>', methods=['PUT'])
def bloquear_usuario(usuario_id):
    if 'usuario_id' not in session or session['rol'] != 3:
        return jsonify({'error': 'Solo administradores'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT idestado FROM estadousuario WHERE descripcionestadousuario = 'bloqueado'")
    bloqueado_id = cur.fetchone()
    
    if bloqueado_id:
        cur.execute("UPDATE usuario SET idestadousuario = %s WHERE idusuario = %s", (bloqueado_id[0], usuario_id))
        conn.commit()
    
    cur.close()
    conn.close()
    return jsonify({'mensaje': 'Usuario bloqueado'})

@app.route('/api/estadisticas', methods=['GET'])
def estadisticas():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 403
    
    if session.get('rol') != 'admin':
        return jsonify({'error': 'Solo administradores'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Total de usuarios (activos)
    cur.execute("SELECT COUNT(*) FROM usuario WHERE idestadousuario = 1")
    total_usuarios = cur.fetchone()[0]
    
    # Total de productos activos
    cur.execute("SELECT COUNT(*) FROM producto WHERE activo = true")
    total_productos = cur.fetchone()[0]
    
    # Ventas completadas
    cur.execute("""
        SELECT COUNT(*) FROM pedido 
        WHERE idestadopedido = (SELECT idestadopedido FROM estadopedido WHERE descripcionestadopedido = 'completado')
    """)
    ventas_completadas = cur.fetchone()[0]
    
    # Total de pedidos
    cur.execute("SELECT COUNT(*) FROM pedido")
    total_pedidos = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return jsonify({
        'total_usuarios': total_usuarios,
        'total_productos': total_productos,
        'ventas_completadas': ventas_completadas,
        'total_pedidos': total_pedidos
    })
# ==================== MENSAJES (SISTEMA DE CHAT) ====================

@app.route('/api/pedidos/<int:pedido_id>/mensajes', methods=['GET'])
def obtener_mensajes(pedido_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesion'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Validar que el usuario participe en el pedido
    cur.execute("SELECT idcliente, idproductor FROM pedido WHERE idpedido = %s", (pedido_id,))
    pedido = cur.fetchone()
    if not pedido or session['usuario_id'] not in (pedido[0], pedido[1]):
        cur.close(); conn.close()
        return jsonify({'error': 'No tienes acceso'}), 403
    
    # Obtener mensajes
    cur.execute("""
        SELECT m.contenidomsj, m.fechaenviomsj, u.primernombre, m.idemisor
        FROM mensaje m
        JOIN usuario u ON m.idemisor = u.idusuario
        WHERE m.idpedido = %s
        ORDER BY m.fechaenviomsj ASC
    """, (pedido_id,))
    
    mensajes = cur.fetchall()
    cur.close(); conn.close()
    
    return jsonify([{
        'contenido': m[0],
        'fecha': m[1],
        'emisor': m[2],
        'es_mio': (m[3] == session['usuario_id'])
    } for m in mensajes])


@app.route('/api/pedidos/<int:pedido_id>/mensajes', methods=['POST'])
def enviar_mensaje(pedido_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesion'}), 401
    
    data = request.json
    contenido = data.get('contenido', '').strip()
    
    if not contenido:
        return jsonify({'error': 'Mensaje vacío'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Identificar quién es el otro usuario para el registro
    cur.execute("SELECT idcliente, idproductor FROM pedido WHERE idpedido = %s", (pedido_id,))
    pedido = cur.fetchone()
    id_receptor = pedido[1] if session['usuario_id'] == pedido[0] else pedido[0]
    
    # Insertar mensaje
    cur.execute("""
        INSERT INTO mensaje (idpedido, idemisor, idreceptor, contenidomsj)
        VALUES (%s, %s, %s, %s)
    """, (pedido_id, session['usuario_id'], id_receptor, contenido))
    
    conn.commit()
    cur.close(); conn.close()
    
    return jsonify({'mensaje': 'Enviado'}), 201


@app.route('/api/pedidos/<int:pedido_id>/mensajes/marcar-leidos', methods=['PUT'])
def marcar_mensajes_leidos(pedido_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesion'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE mensaje SET leido = true 
        WHERE idpedido = %s AND idreceptor = %s
    """, (pedido_id, session['usuario_id']))
    
    conn.commit()
    cur.close(); conn.close()
    return jsonify({'mensaje': 'Leídos'})

# ==================== ACUERDOS ====================

@app.route('/api/pedidos/<int:pedido_id>/acuerdo', methods=['GET'])
def obtener_acuerdo(pedido_id):
    """Obtener el acuerdo actual y verificar si el usuario actual es el creador"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesion'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Verificar que el usuario sea parte del pedido
    cur.execute("SELECT idcliente, idproductor FROM pedido WHERE idpedido = %s", (pedido_id,))
    pedido = cur.fetchone()
    
    if not pedido or session['usuario_id'] not in (pedido[0], pedido[1]):
        cur.close(); conn.close()
        return jsonify({'error': 'No tienes acceso a este pedido'}), 403
    
    # 2. Obtener el acuerdo activo
    cur.execute("""
        SELECT a.idacuerdo, a.precioacordado, a.cantidadacordada, a.estadoacuerdo, a.idcreador
        FROM acuerdo a 
        WHERE a.idpedido = %s AND a.vigenciaacuerdo = true
        ORDER BY a.fechaacordada DESC LIMIT 1
    """, (pedido_id,))
    
    res = cur.fetchone()
    cur.close(); conn.close()
    
    if res:
        return jsonify({
            'tiene_acuerdo': True, 
            'precio': float(res[1]), 
            'cantidad': float(res[2]), 
            'estado': res[3],
            'es_creador': session['usuario_id'] == res[4] # Compara el usuario de la sesión con el creador
        })
        
    return jsonify({'tiene_acuerdo': False})

@app.route('/api/pedidos/<int:pedido_id>/acuerdo', methods=['POST'])
def crear_o_actualizar_acuerdo(pedido_id):
    """Crear o actualizar una negociacion de precio/cantidad"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesion'}), 401
    
    data = request.json
    precio = data.get('precio')
    cantidad = data.get('cantidad')
    
    if not precio or not cantidad:
        return jsonify({'error': 'Faltan precio o cantidad'}), 400
    
    if precio <= 0 or cantidad <= 0:
        return jsonify({'error': 'Precio y cantidad deben ser mayores a 0'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verificar que el usuario sea parte del pedido
    cur.execute("""
        SELECT idcliente, idproductor, idestadopedido FROM pedido WHERE idpedido = %s
    """, (pedido_id,))
    pedido = cur.fetchone()
    
    if not pedido or session['usuario_id'] not in (pedido[0], pedido[1]):
        cur.close()
        conn.close()
        return jsonify({'error': 'No tienes acceso'}), 403
    
    # Verificar que el pedido no este completado o cancelado
    cur.execute("SELECT descripcionestadopedido FROM estadopedido WHERE idestadopedido = %s", (pedido[2],))
    estado_actual = cur.fetchone()
    if estado_actual and estado_actual[0] in ('completado', 'cancelado', 'rechazado'):
        cur.close()
        conn.close()
        return jsonify({'error': f'No se puede negociar, el pedido esta {estado_actual[0]}'}), 400
    
    # Desactivar acuerdos anteriores
    cur.execute("""
        UPDATE acuerdo SET vigenciaacuerdo = false 
        WHERE idpedido = %s AND vigenciaacuerdo = true
    """, (pedido_id,))
    
    # Crear nuevo acuerdo con idcreador
    cur.execute("""
        INSERT INTO acuerdo (idpedido, precioacordado, cantidadacordada, estadoacuerdo, idcreador)
        VALUES (%s, %s, %s, 'pendiente', %s)
        RETURNING idacuerdo
    """, (pedido_id, precio, cantidad, session['usuario_id']))
    
    nuevo_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        'mensaje': 'Propuesta de acuerdo enviada',
        'idacuerdo': nuevo_id,
        'precio': precio,
        'cantidad': cantidad
    }), 201

@app.route('/api/pedidos/<int:pedido_id>/acuerdo/aceptar', methods=['PUT'])
def aceptar_acuerdo(pedido_id):
    """Aceptar el acuerdo propuesto (lo acepta la otra parte)"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesion'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Obtener el acuerdo activo con el idcreador
    cur.execute("""
        SELECT a.idacuerdo, a.precioacordado, a.cantidadacordada, 
               p.idcliente, p.idproductor, a.idcreador
        FROM acuerdo a
        JOIN pedido p ON a.idpedido = p.idpedido
        WHERE a.idpedido = %s AND a.vigenciaacuerdo = true AND a.estadoacuerdo = 'pendiente'
        ORDER BY a.fechaacordada DESC
        LIMIT 1
    """, (pedido_id,))
    
    acuerdo = cur.fetchone()
    
    if not acuerdo:
        cur.close()
        conn.close()
        return jsonify({'error': 'No hay acuerdo pendiente'}), 404
    
    id_acuerdo = acuerdo[0]
    precio_acordado = acuerdo[1]
    cantidad_acordada = acuerdo[2]
    id_cliente = acuerdo[3]
    id_productor = acuerdo[4]
    id_creador = acuerdo[5]
    
    usuario_id = session['usuario_id']
    
    # Verificar que el usuario sea parte del pedido
    if usuario_id not in (id_cliente, id_productor):
        cur.close()
        conn.close()
        return jsonify({'error': 'No eres parte de este pedido'}), 403
    
    # Verificar que el usuario NO sea el creador de la propuesta
    if usuario_id == id_creador:
        cur.close()
        conn.close()
        return jsonify({'error': 'No puedes aceptar tu propia propuesta'}), 400
    
    # Actualizar acuerdo a aceptado
    cur.execute("""
        UPDATE acuerdo SET estadoacuerdo = 'aceptado' 
        WHERE idacuerdo = %s
    """, (id_acuerdo,))
    
    # Actualizar el productopedido con los valores acordados
    cur.execute("""
        UPDATE productopedido 
        SET cantidad = %s, preciounitario = %s 
        WHERE idpedido = %s
    """, (cantidad_acordada, precio_acordado, pedido_id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        'mensaje': 'Acuerdo aceptado',
        'precio': float(precio_acordado),
        'cantidad': float(cantidad_acordada)
    })

@app.route('/api/pedidos/<int:pedido_id>/acuerdo/rechazar', methods=['PUT'])
def rechazar_acuerdo(pedido_id):
    """Rechazar el acuerdo propuesto"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'Inicia sesion'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Obtener el acuerdo activo
    cur.execute("""
        SELECT a.idacuerdo FROM acuerdo a
        WHERE a.idpedido = %s AND a.vigenciaacuerdo = true AND a.estadoacuerdo = 'pendiente'
        ORDER BY a.fechaacordada DESC
        LIMIT 1
    """, (pedido_id,))
    
    acuerdo = cur.fetchone()
    
    if not acuerdo:
        cur.close()
        conn.close()
        return jsonify({'error': 'No hay acuerdo pendiente'}), 404
    
    cur.execute("UPDATE acuerdo SET estadoacuerdo = 'rechazado' WHERE idacuerdo = %s", (acuerdo[0],))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'mensaje': 'Acuerdo rechazado'})



# ==================== INICIO ====================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')