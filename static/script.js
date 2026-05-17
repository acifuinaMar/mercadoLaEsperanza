let usuarioActual = null;
let productosGlobal = [];

// Inicializar
document.addEventListener('DOMContentivoLoaded', () => {
    verificarSesion();
    cargarProductos();
    
    const searchInput = document.getElementById('searchProducto');
    if (searchInput) {
        searchInput.addEventListener('keyup', filtrarProductos);
    }
});

// ==================== AUTENTICACION ====================
async function verificarSesion() {
    try {
        const res = await fetch('/api/verificar-sesion');
        const data = await res.json();
        
        if (data.logueado) {
            usuarioActual = data;
            document.getElementById('authButtons').style.display = 'none';
            document.getElementById('userProfile').style.display = 'flex';
            document.getElementById('userNameDisplay').innerHTML = data.nombre + ' (' + (data.rol === 'productor' ? 'Productor' : data.rol === 'admin' ? 'Admin' : 'Comprador') + ')';
            
            // Mostrar botón de nuevo producto SOLO si es productor
            const nuevoProductoBtn = document.getElementById('nuevoProductoBtn');
            if (nuevoProductoBtn) {
                nuevoProductoBtn.style.display = data.rol === 'productor' ? 'block' : 'none';
            }
            
            // Mostrar pestaña de pedidos para todos los roles
            const pedidosTab = document.getElementById('pedidosTab');
            if (pedidosTab) pedidosTab.style.display = 'block';
            
            // Mostrar pestaña de admin SOLO si es admin
            const adminTab = document.getElementById('adminTab');
            if (adminTab) {
                adminTab.style.display = data.rol === 'admin' ? 'block' : 'none';
            }
            
            if (data.rol === 'admin') {
                cargarAdminPanel();
            }
        } else {
            usuarioActual = null;
            document.getElementById('authButtons').style.display = 'flex';
            document.getElementById('userProfile').style.display = 'none';
            
            const nuevoProductoBtn = document.getElementById('nuevoProductoBtn');
            if (nuevoProductoBtn) nuevoProductoBtn.style.display = 'none';
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// ==================== PRODUCTOS ====================
async function cargarProductos() {
    const container = document.getElementById('listaProductos');
    if (!container) return;
    
    try {
        const res = await fetch('/api/productos');
        if (!res.ok) {
            console.error('Error HTTP:', res.status);
            container.innerHTML = '<div class="loading">Error cargando productos</div>';
            return;
        }
        
        const productos = await res.json();
        console.log('Productos recibidos:', productos);
        
        if (!Array.isArray(productos)) {
            console.error('La respuesta no es un array:', productos);
            container.innerHTML = '<div class="loading">Error en formato de datos</div>';
            return;
        }
        
        mostrarProductos(productos);
    } catch (error) {
        console.error('Error cargando productos:', error);
        container.innerHTML = '<div class="loading">Error de conexion</div>';
    }
}

function mostrarProductos(productos) {
    const container = document.getElementById('listaProductos');
    if (!container) return;
    
    if (!productos || productos.length === 0) {
        container.innerHTML = '<div class="loading">No hay productos disponibles</div>';
        return;
    }
    
    container.innerHTML = productos.map(p => {
        // Valores seguros por si vienen nulos
        const nombre = p.nombreproducto || p.nombre || 'Producto sin nombre';
        const precio = p.precio ? parseFloat(p.precio).toFixed(2) : '0.00';
        const cantidad = p.cantidad_disponible || p.cantidaddisponible || 0;
        const unidad = p.unidad || 'kg';
        const productor = p.productor_nombre || 'Productor';
        const id = p.idproducto || p.id || 0;
        
        let botonesHtml = '';
        
        if (usuarioActual && usuarioActual.rol === 'comprador') {
            botonesHtml = `
                <div style="margin-top: 10px;">
                    <input type="number" id="cant_${id}" placeholder="Cantidad" min="1" max="${cantidad}" style="width: 80px; padding: 5px; margin-right: 5px;">
                    <button class="btn btn-primary btn-small" onclick="hacerPedido(${id})">Comprar</button>
                </div>
            `;
        }
        
        if (usuarioActual && usuarioActual.rol === 'productor' && p.idproductor === usuarioActual.usuario_id) {
            botonesHtml = `
                <div style="margin-top: 10px;">
                    <button class="btn btn-small" onclick="editarProducto(${id})">Editar</button>
                </div>
            `;
        }
        
        return `
            <div class="producto-card" data-nombre="${nombre.toLowerCase()}">
                <div class="producto-nombre">${nombre}</div>
                <div class="producto-precio">Q ${precio}</div>
                <div class="producto-cantidad">${cantidad} ${unidad}</div>
                <div class="producto-productor">Productor: ${productor}</div>
                ${botonesHtml}
            </div>
        `;
    }).join('');
}

function filtrarProductos() {
    const busqueda = document.getElementById('searchProducto');
    if (!busqueda) return;
    
    const termino = busqueda.value.toLowerCase();
    const productos = document.querySelectorAll('.producto-card');
    
    productos.forEach(p => {
        const nombreElement = p.querySelector('.producto-nombre');
        if (nombreElement) {
            const nombre = nombreElement.innerText.toLowerCase();
            p.style.display = nombre.includes(termino) ? 'block' : 'none';
        }
    });
}

async function hacerPedido(productoId) {
    const inputCantidad = document.getElementById('cant_' + productoId);
    if (!inputCantidad) return;
    
    const cantidad = inputCantidad.value;
    if (!cantidad || cantidad <= 0) {
        alert('Ingresa una cantidad valida');
        return;
    }
    
    try {
        const res = await fetch('/api/pedidos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ producto_id: productoId, cantidad: parseFloat(cantidad) })
        });
        
        const data = await res.json();
        if (res.ok) {
            alert(data.mensaje);
            cargarProductos();
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al hacer pedido');
    }
}

// ==================== PEDIDOS ====================
function cambiarTab(tab) {
    const productosTab = document.getElementById('productosTab');
    const pedidosTabContent = document.getElementById('pedidosTabContent');
    const adminTabContent = document.getElementById('adminTabContent');
    
    if (productosTab) productosTab.style.display = 'none';
    if (pedidosTabContent) pedidosTabContent.style.display = 'none';
    if (adminTabContent) adminTabContent.style.display = 'none';
    
    const btns = document.querySelectorAll('.tab-btn');
    btns.forEach(btn => btn.classList.remove('active'));
    
    if (tab === 'productos') {
        if (productosTab) productosTab.style.display = 'block';
        const btn = document.querySelector('.tab-btn');
        if (btn) btn.classList.add('active');
        cargarProductos();
    } else if (tab === 'pedidos') {
        if (pedidosTabContent) pedidosTabContent.style.display = 'block';
        const pedidosTabBtn = document.getElementById('pedidosTabBtn');
        if (pedidosTabBtn) pedidosTabBtn.classList.add('active');
        cargarMisPedidos();
    } else if (tab === 'admin') {
        if (adminTabContent) adminTabContent.style.display = 'block';
        const adminTab = document.getElementById('adminTab');
        if (adminTab) adminTab.classList.add('active');
        cargarAdminPanel();
    }
}

async function cargarMisPedidos() {
    const container = document.getElementById('listaPedidos');
    if (!container) return;
    
    try {
        const res = await fetch('/api/mis-pedidos');
        const pedidos = await res.json();
        
        if (!pedidos.length) {
            container.innerHTML = '<div class="loading">No tienes pedidos</div>';
            return;
        }
        
        container.innerHTML = pedidos.map(p => {
            const esProductor = usuarioActual && usuarioActual.rol === 'productor';
            // Asegurar que el nombre no sea null o undefined
            const nombreContraparte = p.contraparte_nombre || (esProductor ? 'Comprador' : 'Productor');
            
            let botonesHtml = '';
            if (p.estado === 'pendiente' && esProductor) {
                botonesHtml = `
                    <div style="margin-top: 10px;">
                        <button class="btn btn-success btn-small" onclick="gestionarPedido(${p.idpedido}, 'aceptado')">Aceptar</button>
                        <button class="btn btn-danger btn-small" onclick="gestionarPedido(${p.idpedido}, 'rechazado')">Rechazar</button>
                    </div>
                `;
            }
            
            if (p.estado === 'aceptado') {
                botonesHtml = `
                    <div style="margin-top: 10px;">
                        <button class="btn btn-primary btn-small" onclick="confirmarEntrega(${p.idpedido})">Confirmar Entrega</button>
                    </div>
                `;
            }
            
            if (p.estado === 'completado') {
                botonesHtml = `
                    <div style="margin-top: 10px;">
                        <button class="btn btn-small" onclick="calificarUsuario(${p.idpedido}, ${p.contraparte_id || 0})">Calificar</button>
                    </div>
                `;
            }
            
            return `
            <div class="pedido-card">
                <strong>${p.producto_nombre}</strong> - ${p.cantidad_solicitada} unidades
                <div>Precio: Q${parseFloat(p.precio).toFixed(2)}</div>
                <div><span class="pedido-estado estado-${p.estado}">${(p.estado || 'pendiente').toUpperCase()}</span></div>
                <div>${esProductor ? 'Comprador' : 'Productor'}: ${nombreContraparte}</div>
                <div style="margin-top: 10px;">
                    <button class="btn btn-small" onclick="abrirChat(${p.idpedido}, '${p.producto_nombre}')">Negociar</button>
                    ${botonesHtml}
                </div>
            </div>
        `;
        }).join('');
    } catch (error) {
        console.error('Error cargando pedidos:', error);
        container.innerHTML = '<div class="loading">Error cargando pedidos</div>';
    }
}

async function gestionarPedido(pedidoId, estado) {
    try {
        const res = await fetch('/api/pedidos/' + pedidoId + '/gestionar', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ estado: estado })
        });
        const data = await res.json();
        alert(data.mensaje || (res.ok ? 'Procesado' : 'Error'));
        if (res.ok) cargarMisPedidos();
    } catch (error) {
        console.error('Error:', error);
        alert('Error al gestionar pedido');
    }
}

// ==================== AUTENTICACION (funciones de UI) ====================
function mostrarLogin() {
    const modal = document.getElementById('loginModal');
    if (modal) modal.style.display = 'flex';
}

function mostrarRegistro() {
    const modal = document.getElementById('registroModal');
    if (modal) modal.style.display = 'flex';
}

function cerrarModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
}

async function iniciarSesion() {
    const email = document.getElementById('loginEmail');
    const password = document.getElementById('loginPassword');
    
    if (!email || !password) return;
    
    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email.value, contrasena: password.value })
        });
        const data = await res.json();
        
        if (res.ok) {
            alert(data.mensaje);
            cerrarModal('loginModal');
            verificarSesion();
            cargarProductos();
            email.value = '';
            password.value = '';
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexion');
    }
}

async function registrarse() {
    const dpi = document.getElementById('regDPI');
    const primerNombre = document.getElementById('regPrimerNombre');
    const primerApellido = document.getElementById('regPrimerApellido');
    const telefono = document.getElementById('regTelefono');
    const email = document.getElementById('regEmail');
    const password = document.getElementById('regPassword');
    const rol = document.getElementById('regRol');
    
    if (!dpi || !primerNombre || !primerApellido || !telefono || !email || !password || !rol) return;
    
    const data = {
        dpi: dpi.value,
        primerNombre: primerNombre.value,
        segundoNombre: document.getElementById('regSegundoNombre') ? document.getElementById('regSegundoNombre').value : null,
        primerApellido: primerApellido.value,
        segundoApellido: document.getElementById('regSegundoApellido') ? document.getElementById('regSegundoApellido').value : null,
        telefono: telefono.value,
        email: email.value,
        contrasena: password.value,
        rol: rol.value
    };
    
    if (!data.dpi || !data.primerNombre || !data.primerApellido || !data.telefono || !data.email || !data.contrasena) {
        alert('Completa todos los campos obligatorios');
        return;
    }
    
    if (data.dpi.length < 13) {
        alert('DPI debe tener 13 digitos');
        return;
    }
    
    try {
        const res = await fetch('/api/registro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        
        if (res.ok) {
            alert(result.mensaje + '\nAhora puedes iniciar sesion');
            cerrarModal('registroModal');
            mostrarLogin();
            
            // Limpiar formulario
            dpi.value = '';
            primerNombre.value = '';
            if (document.getElementById('regSegundoNombre')) document.getElementById('regSegundoNombre').value = '';
            primerApellido.value = '';
            if (document.getElementById('regSegundoApellido')) document.getElementById('regSegundoApellido').value = '';
            telefono.value = '';
            email.value = '';
            password.value = '';
        } else {
            alert(result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexion');
    }
}

async function cerrarSesion() {
    await fetch('/api/logout', { method: 'POST' });
    usuarioActual = null;
    verificarSesion();
    cargarProductos();
    cambiarTab('productos');
}

// ==================== PRODUCTOR ====================
function mostrarNuevoProducto() {
    const modal = document.getElementById('productoModal');
    if (modal) modal.style.display = 'flex';
}

async function crearProducto() {
    const nombre = document.getElementById('prodNombre');
    const descripcion = document.getElementById('prodDesc');
    const precio = document.getElementById('prodPrecio');
    const cantidad = document.getElementById('prodCantidad');
    const unidad = document.getElementById('prodUnidad');
    
    if (!nombre || !precio || !cantidad) return;
    
    const data = {
        nombre: nombre.value,
        descripcion: descripcion ? descripcion.value : '',
        precio: parseFloat(precio.value),
        cantidad: parseFloat(cantidad.value),
        unidad: unidad ? unidad.value : 'kg'
    };
    
    if (!data.nombre || !data.precio || !data.cantidad) {
        alert('Completa todos los campos');
        return;
    }
    
    try {
        const res = await fetch('/api/productos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        
        if (res.ok) {
            alert(result.mensaje);
            cerrarModal('productoModal');
            cargarProductos();
            nombre.value = '';
            if (descripcion) descripcion.value = '';
            precio.value = '';
            cantidad.value = '';
        } else {
            alert(result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al crear producto');
    }
}

// ==================== ADMIN ====================
async function cargarAdminPanel() {
    await cargarEstadisticas();
    await cargarReportes();
}

async function cargarEstadisticas() {
    const container = document.getElementById('estadisticas');
    if (!container) return;
    
    try {
        const res = await fetch('/api/estadisticas');
        const stats = await res.json();
        
        container.innerHTML = `
            <div class="stat-card"><div class="stat-number">${stats.total_usuarios || 0}</div><div>Usuarios</div></div>
            <div class="stat-card"><div class="stat-number">${stats.total_productos || 0}</div><div>Productos</div></div>
            <div class="stat-card"><div class="stat-number">${stats.ventas_completadas || 0}</div><div>Ventas</div></div>
        `;
    } catch (error) {
        console.error('Error stats:', error);
        container.innerHTML = '<div class="loading">Error cargando estadisticas</div>';
    }
}

async function cargarReportes() {
    const container = document.getElementById('reportesLista');
    if (!container) return;
    
    try {
        const res = await fetch('/api/admin/reportes');
        const reportes = await res.json();
        
        if (!reportes.length) {
            container.innerHTML = '<div class="loading">No hay reportes pendientes</div>';
            return;
        }
        
        container.innerHTML = reportes.map(r => `
            <div class="pedido-card" style="border-left-color: #f44336;">
                <strong>Reporte contra: ${r.reportado_nombre}</strong>
                <div>Motivo: ${r.motivo}</div>
                <div>Reportado por: ${r.reportante_nombre}</div>
                <button class="btn btn-danger btn-small" onclick="bloquearUsuario(${r.usuario_reportado})">Bloquear usuario</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error reportes:', error);
        container.innerHTML = '<div class="loading">Error cargando reportes</div>';
    }
}

async function bloquearUsuario(usuarioId) {
    if (!confirm('Bloquear este usuario? No podra iniciar sesion.')) return;
    try {
        const res = await fetch('/api/admin/bloquear/' + usuarioId, { method: 'PUT' });
        const data = await res.json();
        alert(data.mensaje);
        cargarReportes();
    } catch (error) {
        console.error('Error:', error);
        alert('Error al bloquear');
    }
}

function calificarUsuario(pedidoId, calificadoId) {
    const puntuacion = prompt('Califica del 1 al 5:\n1=Malo, 3=Regular, 5=Excelente');
    if (!puntuacion || puntuacion < 1 || puntuacion > 5) return;
    
    fetch('/api/calificar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            pedido_id: pedidoId, 
            calificado_id: calificadoId, 
            puntuacion: parseInt(puntuacion),
            comentario: ''
        })
    }).then(async res => {
        const data = await res.json();
        alert(data.mensaje || (res.ok ? 'Gracias por calificar' : 'Error'));
        if (res.ok) cargarMisPedidos();
    }).catch(error => {
        console.error('Error:', error);
        alert('Error al calificar');
    });
}

// ==================== CHAT Y NEGOCIACION ====================

let pedidoActual = null;

async function abrirChat(pedidoId, productoNombre) {
    pedidoActual = pedidoId;
    document.getElementById('chatProductoNombre').innerText = productoNombre;
    document.getElementById('chatModal').style.display = 'flex';
    
    // Cargar mensajes
    await cargarMensajes();
    
    // Cargar acuerdo actual
    await cargarAcuerdo();
}

async function cargarMensajes() {
    if (!pedidoActual) return;
    
    const container = document.getElementById('chatMensajes');
    container.innerHTML = '<div style="text-align: center;">Cargando mensajes...</div>';
    
    try {
        const res = await fetch(`/api/pedidos/${pedidoActual}/mensajes`);
        const mensajes = await res.json();
        
        if (!mensajes.length) {
            container.innerHTML = '<div style="text-align: center; color: #999;">No hay mensajes. Envia uno para empezar!</div>';
            return;
        }
        
        container.innerHTML = mensajes.map(m => `
            <div style="margin-bottom: 10px; text-align: ${m.es_mio ? 'right' : 'left'};">
                <div style="display: inline-block; background: ${m.es_mio ? '#4caf50' : '#ddd'}; color: ${m.es_mio ? 'white' : 'black'}; padding: 8px 12px; border-radius: 12px; max-width: 80%;">
                    <div style="font-size: 11px; opacity: 0.7;">${m.emisor_nombre}</div>
                    <div>${m.contenido}</div>
                    <div style="font-size: 10px; opacity: 0.5;">${new Date(m.fecha).toLocaleTimeString()}</div>
                </div>
            </div>
        `).join('');
        
        container.scrollTop = container.scrollHeight;
        
        // Marcar como leidos
        await fetch(`/api/pedidos/${pedidoActual}/mensajes/marcar-leidos`, { method: 'PUT' });
        
    } catch (error) {
        console.error('Error cargando mensajes:', error);
        container.innerHTML = '<div style="text-align: center; color: red;">Error cargando mensajes</div>';
    }
}

async function enviarMensaje() {
    const input = document.getElementById('chatMensajeInput');
    const contenido = input.value.trim();
    
    if (!contenido || !pedidoActual) return;
    
    try {
        const res = await fetch(`/api/pedidos/${pedidoActual}/mensajes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contenido: contenido })
        });
        
        if (res.ok) {
            input.value = '';
            await cargarMensajes();
        } else {
            const data = await res.json();
            alert(data.error || 'Error al enviar mensaje');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexion');
    }
}

async function cargarAcuerdo() {
    if (!pedidoActual) return;
    
    try {
        const res = await fetch(`/api/pedidos/${pedidoActual}/acuerdo`);
        const acuerdo = await res.json();
        
        const infoDiv = document.getElementById('chatAcuerdoInfo');
        const negBotones = document.getElementById('negBotones');
        
        if (acuerdo.tiene_acuerdo) {
            infoDiv.innerHTML = `Precio: Q${acuerdo.precio} | Cantidad: ${acuerdo.cantidad} | Estado: ${acuerdo.estado}`;
            
            if (acuerdo.estado === 'pendiente') {
                negBotones.style.display = 'block';
            } else {
                negBotones.style.display = 'none';
            }
        } else {
            infoDiv.innerHTML = 'Sin acuerdo - Envia una propuesta para negociar';
            negBotones.style.display = 'none';
        }
    } catch (error) {
        console.error('Error cargando acuerdo:', error);
    }
}

async function enviarPropuesta() {
    const precio = document.getElementById('negPrecio').value;
    const cantidad = document.getElementById('negCantidad').value;
    
    if (!precio || !cantidad) {
        alert('Ingresa precio y cantidad');
        return;
    }
    
    try {
        const res = await fetch(`/api/pedidos/${pedidoActual}/acuerdo`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ precio: parseFloat(precio), cantidad: parseFloat(cantidad) })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            alert('Propuesta enviada! Espera a que la otra parte la acepte.');
            document.getElementById('negPrecio').value = '';
            document.getElementById('negCantidad').value = '';
            await cargarAcuerdo();
            // Enviar mensaje automatico
            await fetch(`/api/pedidos/${pedidoActual}/mensajes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contenido: `Propuesta de acuerdo: Q${precio} por ${cantidad} unidades` })
            });
            await cargarMensajes();
        } else {
            alert(data.error || 'Error al enviar propuesta');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexion');
    }
}

async function aceptarAcuerdo() {
    if (!confirm('¿Aceptar este acuerdo? El pedido se actualizara con el nuevo precio y cantidad.')) return;
    
    try {
        const res = await fetch(`/api/pedidos/${pedidoActual}/acuerdo/aceptar`, { method: 'PUT' });
        const data = await res.json();
        
        if (res.ok) {
            alert('Acuerdo aceptado! El pedido ha sido actualizado.');
            await cargarAcuerdo();
            await cargarMisPedidos();
            // Enviar mensaje automatico
            await fetch(`/api/pedidos/${pedidoActual}/mensajes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contenido: 'He aceptado el acuerdo!' })
            });
            await cargarMensajes();
        } else {
            alert(data.error || 'Error al aceptar acuerdo');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexion');
    }
}

async function rechazarAcuerdo() {
    if (!confirm('¿Rechazar este acuerdo? La otra parte podra hacer una nueva propuesta.')) return;
    
    try {
        const res = await fetch(`/api/pedidos/${pedidoActual}/acuerdo/rechazar`, { method: 'PUT' });
        const data = await res.json();
        
        if (res.ok) {
            alert('Acuerdo rechazado');
            await cargarAcuerdo();
            // Enviar mensaje automatico
            await fetch(`/api/pedidos/${pedidoActual}/mensajes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contenido: 'He rechazado el acuerdo, podemos negociar de nuevo' })
            });
            await cargarMensajes();
        } else {
            alert(data.error || 'Error al rechazar acuerdo');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexion');
    }
}

// Cerrar modal al hacer clic fuera
window.onclick = function(event) {
    if (event.target.classList && event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}