-- =====================================================
-- SISTEMA MERCADO LA ESPERANZA
-- Script completo de base de datos
-- =====================================================

-- =====================================================
-- 1. TABLAS CATALOGO (con verificación de existencia)
-- =====================================================

-- Tipos de usuario
CREATE TABLE IF NOT EXISTS tipousuario (
    idtipousuario SERIAL PRIMARY KEY,
    descripciontipousuario VARCHAR(50) NOT NULL UNIQUE
);

-- Estados de usuario
CREATE TABLE IF NOT EXISTS estadousuario (
    idestado SERIAL PRIMARY KEY,
    descripcionestadousuario VARCHAR(30) NOT NULL UNIQUE
);

-- Estados de pedido
CREATE TABLE IF NOT EXISTS estadopedido (
    idestadopedido SERIAL PRIMARY KEY,
    descripcionestadopedido VARCHAR(30) NOT NULL UNIQUE
);

-- Estados de entrega
CREATE TABLE IF NOT EXISTS estadoentrega (
    idestadoentrega SERIAL PRIMARY KEY,
    descripcionestadoentrega VARCHAR(30) NOT NULL UNIQUE
);

-- Unidades de medida
CREATE TABLE IF NOT EXISTS unidadmedida (
    idunidad SERIAL PRIMARY KEY,
    nombreunidad VARCHAR(50) NOT NULL,
    abreviatura VARCHAR(10) NOT NULL
);

-- Puntos de entrega
CREATE TABLE IF NOT EXISTS puntoentrega (
    idpuntoentrega SERIAL PRIMARY KEY,
    nombrepunto VARCHAR(100) NOT NULL,
    ubicacion TEXT NOT NULL,
    descripcionpunto TEXT
);

-- =====================================================
-- 2. TABLA USUARIO
-- =====================================================

CREATE TABLE IF NOT EXISTS usuario (
    idusuario SERIAL PRIMARY KEY,
    dpiusuario VARCHAR(20) NOT NULL UNIQUE,
    primernombre VARCHAR(50) NOT NULL,
    segundonombre VARCHAR(50),
    primerapellido VARCHAR(50) NOT NULL,
    segundoapellido VARCHAR(50),
    telefonousuario VARCHAR(15) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    tipousuario INTEGER NOT NULL REFERENCES tipousuario(idtipousuario),
    idestadousuario INTEGER NOT NULL REFERENCES estadousuario(idestado),
    fecharegistro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 3. TABLA PRODUCTO
-- =====================================================

CREATE TABLE IF NOT EXISTS producto (
    idproducto SERIAL PRIMARY KEY,
    nombreproducto VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio NUMERIC(10,2) NOT NULL,
    idunidadmedida INTEGER NOT NULL REFERENCES unidadmedida(idunidad),
    idproductor INTEGER NOT NULL REFERENCES usuario(idusuario),
    activo BOOLEAN DEFAULT TRUE,
    fecharegistro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cantidaddisponible NUMERIC(10,2) DEFAULT 0 NOT NULL
);

-- =====================================================
-- 4. TABLA PEDIDO
-- =====================================================

CREATE TABLE IF NOT EXISTS pedido (
    idpedido SERIAL PRIMARY KEY,
    idcliente INTEGER NOT NULL REFERENCES usuario(idusuario),
    idproductor INTEGER NOT NULL REFERENCES usuario(idusuario),
    fechasolicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    idestadopedido INTEGER NOT NULL REFERENCES estadopedido(idestadopedido)
);

-- =====================================================
-- 5. TABLA PRODUCTOPEDIDO
-- =====================================================

CREATE TABLE IF NOT EXISTS productopedido (
    idproductopedido SERIAL PRIMARY KEY,
    idpedido INTEGER NOT NULL REFERENCES pedido(idpedido) ON DELETE CASCADE,
    idproducto INTEGER NOT NULL REFERENCES producto(idproducto),
    cantidad NUMERIC(10,2) NOT NULL CHECK (cantidad > 0),
    preciounitario NUMERIC(10,2) NOT NULL CHECK (preciounitario >= 0)
);

-- =====================================================
-- 6. TABLA ACUERDO
-- =====================================================

CREATE TABLE IF NOT EXISTS acuerdo (
    idacuerdo SERIAL PRIMARY KEY,
    idpedido INTEGER NOT NULL REFERENCES pedido(idpedido) ON DELETE CASCADE,
    precioacordado NUMERIC(10,2) NOT NULL CHECK (precioacordado >= 0),
    cantidadacordada NUMERIC(10,2) NOT NULL CHECK (cantidadacordada > 0),
    fechaacordada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estadoacuerdo VARCHAR(20) DEFAULT 'pendiente',
    vigenciaacuerdo BOOLEAN DEFAULT TRUE,
    idcreador INTEGER REFERENCES usuario(idusuario)
);

-- =====================================================
-- 7. TABLA MENSAJE
-- =====================================================

CREATE TABLE IF NOT EXISTS mensaje (
    idmensaje SERIAL PRIMARY KEY,
    idpedido INTEGER NOT NULL REFERENCES pedido(idpedido) ON DELETE CASCADE,
    idemisor INTEGER NOT NULL REFERENCES usuario(idusuario),
    idreceptor INTEGER NOT NULL REFERENCES usuario(idusuario),
    contenidomsj TEXT NOT NULL,
    fechaenviomsj TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    leido BOOLEAN DEFAULT FALSE
);

-- =====================================================
-- 8. TABLA CALIFICACION
-- =====================================================

CREATE TABLE IF NOT EXISTS calificacion (
    idcalificacion SERIAL PRIMARY KEY,
    idpedido INTEGER NOT NULL REFERENCES pedido(idpedido) ON DELETE CASCADE,
    idcalificador INTEGER NOT NULL REFERENCES usuario(idusuario),
    idcalificado INTEGER NOT NULL REFERENCES usuario(idusuario),
    puntaje INTEGER NOT NULL CHECK (puntaje >= 1 AND puntaje <= 5),
    comentario TEXT,
    fechacalificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(idpedido, idcalificador)
);

-- =====================================================
-- 9. TABLA ENTREGA
-- =====================================================

CREATE TABLE IF NOT EXISTS entrega (
    identrega SERIAL PRIMARY KEY,
    idpedido INTEGER NOT NULL REFERENCES pedido(idpedido) ON DELETE CASCADE,
    idpuntoentrega INTEGER NOT NULL REFERENCES puntoentrega(idpuntoentrega),
    fechaentrega TIMESTAMP,
    confirmadoproductor BOOLEAN DEFAULT FALSE,
    confirmadocliente BOOLEAN DEFAULT FALSE,
    idestadoentrega INTEGER NOT NULL REFERENCES estadoentrega(idestadoentrega),
    fechaconfirmacionproductor TIMESTAMP,
    fechaconfirmacioncliente TIMESTAMP
);

-- =====================================================
-- 10. TABLA HISTORIALPEDIDO
-- =====================================================

CREATE TABLE IF NOT EXISTS historialpedido (
    idhistorial SERIAL PRIMARY KEY,
    idpedido INTEGER NOT NULL REFERENCES pedido(idpedido) ON DELETE CASCADE,
    estadohistorialpedido VARCHAR(30) NOT NULL,
    fechacambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comentario TEXT
);

-- =====================================================
-- 11. TABLA REPORTE
-- =====================================================

CREATE TABLE IF NOT EXISTS reporte (
    idreporte SERIAL PRIMARY KEY,
    idemisor INTEGER NOT NULL REFERENCES usuario(idusuario),
    idreceptor INTEGER NOT NULL REFERENCES usuario(idusuario),
    comentarioreporte TEXT NOT NULL,
    fechaenviorprt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'pendiente'
);

-- =====================================================
-- 12. DATOS INICIALES (CATALOGOS)
-- =====================================================

-- Tipos de usuario
INSERT INTO tipousuario (descripciontipousuario) VALUES 
    ('productor'), 
    ('comprador'), 
    ('admin')
ON CONFLICT (descripciontipousuario) DO NOTHING;

-- Estados de usuario
INSERT INTO estadousuario (descripcionestadousuario) VALUES 
    ('activo'), 
    ('bloqueado'), 
    ('suspendido')
ON CONFLICT (descripcionestadousuario) DO NOTHING;

-- Estados de pedido
INSERT INTO estadopedido (descripcionestadopedido) VALUES 
    ('pendiente'), 
    ('aceptado'), 
    ('rechazado'), 
    ('completado'), 
    ('cancelado')
ON CONFLICT (descripcionestadopedido) DO NOTHING;

-- Estados de entrega
INSERT INTO estadoentrega (descripcionestadoentrega) VALUES 
    ('pendiente'), 
    ('en_proceso'), 
    ('entregado'), 
    ('incidente')
ON CONFLICT (descripcionestadoentrega) DO NOTHING;

-- Unidades de medida
INSERT INTO unidadmedida (nombreunidad, abreviatura) VALUES 
    ('Kilogramos', 'kg'),
    ('Libras', 'lb'),
    ('Unidades', 'und'),
    ('Quintales', 'qq'),
    ('Manojos', 'manojo')
ON CONFLICT (idunidad) DO NOTHING;

-- Puntos de entrega
INSERT INTO puntoentrega (nombrepunto, ubicacion, descripcionpunto) VALUES 
    ('Parque Central', 'Frente a la iglesia', 'Punto de encuentro principal'),
    ('Mercado Municipal', 'Zona de empaques', 'Entrega en mercado los sabados'),
    ('Bodega Comunitaria', 'Final de la calle principal', 'Centro de acopio')
ON CONFLICT (idpuntoentrega) DO NOTHING;
