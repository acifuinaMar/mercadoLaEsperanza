-- database.sql - Modelo completo según tu diseño
CREATE DATABASE comunidad_agro;

\c comunidad_agro;

-- =====================================================
-- 1. TABLAS CATÁLOGO
-- =====================================================

CREATE TABLE TipoUsuario (
    idTipoUsuario SERIAL PRIMARY KEY,
    descripcionTipoUsuario VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE EstadoUsuario (
    idEstado SERIAL PRIMARY KEY,
    descripcionEstadoUsuario VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE UnidadMedida (
    idUnidad SERIAL PRIMARY KEY,
    nombreUnidad VARCHAR(50) NOT NULL,
    abreviatura VARCHAR(10) NOT NULL
);

CREATE TABLE EstadoPedido (
    idEstadoPedido SERIAL PRIMARY KEY,
    descripcionEstadoPedido VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE EstadoEntrega (
    idEstadoEntrega SERIAL PRIMARY KEY,
    descripcionEstadoEntrega VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE PuntoEntrega (
    idPuntoEntrega SERIAL PRIMARY KEY,
    nombrePunto VARCHAR(100) NOT NULL,
    ubicacion TEXT NOT NULL,
    descripcionPunto TEXT
);

-- =====================================================
-- 2. TABLA PRINCIPAL USUARIO
-- =====================================================

CREATE TABLE Usuario (
    idUsuario SERIAL PRIMARY KEY,
    dpiUsuario VARCHAR(20) UNIQUE NOT NULL,
    primerNombre VARCHAR(50) NOT NULL,
    segundoNombre VARCHAR(50),
    primerApellido VARCHAR(50) NOT NULL,
    segundoApellido VARCHAR(50),
    telefonoUsuario VARCHAR(15) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    tipoUsuario INT NOT NULL REFERENCES TipoUsuario(idTipoUsuario),
    idEstadoUsuario INT NOT NULL REFERENCES EstadoUsuario(idEstado),
    fechaRegistro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 3. TABLAS DE NEGOCIO
-- =====================================================

CREATE TABLE Producto (
    idProducto SERIAL PRIMARY KEY,
    nombreProducto VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL,
    idUnidadMedida INT NOT NULL REFERENCES UnidadMedida(idUnidad),
    idProductor INT NOT NULL REFERENCES Usuario(idUsuario),
    activo BOOLEAN DEFAULT TRUE,
    fechaRegistro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Pedido (
    idPedido SERIAL PRIMARY KEY,
    idCliente INT NOT NULL REFERENCES Usuario(idUsuario),
    idProductor INT NOT NULL REFERENCES Usuario(idUsuario),
    fechaSolicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    idEstadoPedido INT NOT NULL REFERENCES EstadoPedido(idEstadoPedido)
);

CREATE TABLE ProductoPedido (
    idProductoPedido SERIAL PRIMARY KEY,
    idPedido INT NOT NULL REFERENCES Pedido(idPedido) ON DELETE CASCADE,
    idProducto INT NOT NULL REFERENCES Producto(idProducto),
    cantidad DECIMAL(10,2) NOT NULL,
    precioUnitario DECIMAL(10,2) NOT NULL, -- Precio vigente al momento del pedido
    CHECK (cantidad > 0),
    CHECK (precioUnitario >= 0)
);

CREATE TABLE Acuerdo (
    idAcuerdo SERIAL PRIMARY KEY,
    idPedido INT NOT NULL REFERENCES Pedido(idPedido) ON DELETE CASCADE,
    precioAcordado DECIMAL(10,2) NOT NULL,
    cantidadAcordada DECIMAL(10,2) NOT NULL,
    fechaAcordada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estadoAcuerdo VARCHAR(20) DEFAULT 'pendiente', -- pendiente, aceptado, rechazado
    vigenciaAcuerdo BOOLEAN DEFAULT TRUE,
    CHECK (precioAcordado >= 0),
    CHECK (cantidadAcordada > 0)
);

CREATE TABLE Entrega (
    idEntrega SERIAL PRIMARY KEY,
    idPedido INT NOT NULL REFERENCES Pedido(idPedido) ON DELETE CASCADE,
    idPuntoEntrega INT NOT NULL REFERENCES PuntoEntrega(idPuntoEntrega),
    fechaEntrega TIMESTAMP,
    confirmadoProductor BOOLEAN DEFAULT FALSE,
    confirmadoCliente BOOLEAN DEFAULT FALSE,
    idEstadoEntrega INT NOT NULL REFERENCES EstadoEntrega(idEstadoEntrega),
    fechaConfirmacionProductor TIMESTAMP,
    fechaConfirmacionCliente TIMESTAMP
);

CREATE TABLE HistorialPedido (
    idHistorial SERIAL PRIMARY KEY,
    idPedido INT NOT NULL REFERENCES Pedido(idPedido) ON DELETE CASCADE,
    estadoHistorialPedido VARCHAR(30) NOT NULL,
    fechaCambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comentario TEXT
);

CREATE TABLE Mensaje (
    idMensaje SERIAL PRIMARY KEY,
    idPedido INT NOT NULL REFERENCES Pedido(idPedido) ON DELETE CASCADE,
    idEmisor INT NOT NULL REFERENCES Usuario(idUsuario),
    idReceptor INT NOT NULL REFERENCES Usuario(idUsuario),
    contenidoMsj TEXT NOT NULL,
    fechaEnvioMsj TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    leido BOOLEAN DEFAULT FALSE
);

CREATE TABLE Calificacion (
    idCalificacion SERIAL PRIMARY KEY,
    idPedido INT NOT NULL REFERENCES Pedido(idPedido) ON DELETE CASCADE,
    idCalificador INT NOT NULL REFERENCES Usuario(idUsuario),
    idCalificado INT NOT NULL REFERENCES Usuario(idUsuario),
    puntaje INT NOT NULL CHECK (puntaje >= 1 AND puntaje <= 5),
    comentario TEXT,
    fechaCalificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(idPedido, idCalificador) -- Un usuario solo califica una vez por pedido
);

CREATE TABLE Reporte (
    idReporte SERIAL PRIMARY KEY,
    idEmisor INT NOT NULL REFERENCES Usuario(idUsuario),
    idReceptor INT NOT NULL REFERENCES Usuario(idUsuario),
    comentarioReporte TEXT NOT NULL,
    fechaEnvioRprt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'pendiente' -- pendiente, revisado, resuelto
);

-- =====================================================
-- 4. CATÁLOGOS
-- =====================================================

-- Tipos de usuario
INSERT INTO TipoUsuario (descripcionTipoUsuario) VALUES 
    ('productor'),
    ('comprador'),
    ('admin');

-- Estados de usuario
INSERT INTO EstadoUsuario (descripcionEstadoUsuario) VALUES 
    ('activo'),
    ('bloqueado'),
    ('suspendido');

-- Unidades de medida
INSERT INTO UnidadMedida (nombreUnidad, abreviatura) VALUES 
    ('Kilogramos', 'kg'),
    ('Libras', 'lb'),
    ('Unidades', 'und'),
    ('Quintales', 'qq'),
    ('Manojos', 'manojo');

-- Estados de pedido
INSERT INTO EstadoPedido (descripcionEstadoPedido) VALUES 
    ('pendiente'),
    ('aceptado'),
    ('rechazado'),
    ('completado'),
    ('cancelado');

-- Estados de entrega
INSERT INTO EstadoEntrega (descripcionEstadoEntrega) VALUES 
    ('pendiente'),
    ('en_proceso'),
    ('entregado'),
    ('incidente');

-- Puntos de entrega (para ejemplo)
INSERT INTO PuntoEntrega (nombrePunto, ubicacion, descripcionPunto) VALUES 
    ('Parque Central', 'Frente a la iglesia', 'Punto de encuentro principal'),
    ('Mercado Municipal', 'Zona de empaques', 'Entrega en mercado los sábados'),
    ('Bodega Comunitaria', 'Final de la calle principal', 'Centro de acopio');

-- Usuario administrador por defecto
INSERT INTO Usuario (dpiUsuario, primerNombre, segundoNombre, primerApellido, segundoApellido, telefonoUsuario, email, contrasena, tipoUsuario, idEstadoUsuario)
VALUES (
    'ADMIN1',
    'Administrador',
    NULL,
    'Sistema',
    NULL,
    '00000000',
    'admin@comunidad.com',
    'admin123',
    (SELECT idTipoUsuario FROM TipoUsuario WHERE descripcionTipoUsuario = 'admin'),
    (SELECT idEstado FROM EstadoUsuario WHERE descripcionEstadoUsuario = 'activo')
);