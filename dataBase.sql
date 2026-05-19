---------------------------------------------------------------------
-- 1. CREACIÓN DE TABLAS MAESTRAS / INDEPENDIENTES
---------------------------------------------------------------------

-- Tabla: tipousuario
CREATE TABLE public.tipousuario (
    idtipousuario integer NOT NULL,
    descripciontipousuario character varying(50) NOT NULL
);

CREATE SEQUENCE public.tipousuario_idtipousuario_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.tipousuario_idtipousuario_seq OWNED BY public.tipousuario.idtipousuario;
ALTER TABLE ONLY public.tipousuario ALTER COLUMN idtipousuario SET DEFAULT nextval('public.tipousuario_idtipousuario_seq'::regclass);
ALTER TABLE ONLY public.tipousuario ADD CONSTRAINT tipousuario_pkey PRIMARY KEY (idtipousuario);
ALTER TABLE ONLY public.tipousuario ADD CONSTRAINT tipousuario_descripciontipousuario_key UNIQUE (descripciontipousuario);

-- Tabla: estadousuario
CREATE TABLE public.estadousuario (
    idestado integer NOT NULL,
    descripcionestadousuario character varying(30) NOT NULL
);

CREATE SEQUENCE public.estadousuario_idestado_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.estadousuario_idestado_seq OWNED BY public.estadousuario.idestado;
ALTER TABLE ONLY public.estadousuario ALTER COLUMN idestado SET DEFAULT nextval('public.estadousuario_idestado_seq'::regclass);
ALTER TABLE ONLY public.estadousuario ADD CONSTRAINT estadousuario_pkey PRIMARY KEY (idestado);
ALTER TABLE ONLY public.estadousuario ADD CONSTRAINT estadousuario_descripcionestadousuario_key UNIQUE (descripcionestadousuario);

-- Tabla: estadopedido
CREATE TABLE public.estadopedido (
    idestadopedido integer NOT NULL,
    descripcionestadopedido character varying(30) NOT NULL
);

CREATE SEQUENCE public.estadopedido_idestadopedido_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.estadopedido_idestadopedido_seq OWNED BY public.estadopedido.idestadopedido;
ALTER TABLE ONLY public.estadopedido ALTER COLUMN idestadopedido SET DEFAULT nextval('public.estadopedido_idestadopedido_seq'::regclass);
ALTER TABLE ONLY public.estadopedido ADD CONSTRAINT estadopedido_pkey PRIMARY KEY (idestadopedido);
ALTER TABLE ONLY public.estadopedido ADD CONSTRAINT estadopedido_descripcionestadopedido_key UNIQUE (descripcionestadopedido);


-- Tabla: estadoentrega
CREATE TABLE public.estadoentrega (
    idestadoentrega integer NOT NULL,
    descripcionestadoentrega character varying(30) NOT NULL
);

CREATE SEQUENCE public.estadoentrega_idestadoentrega_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.estadoentrega_idestadoentrega_seq OWNED BY public.estadoentrega.idestadoentrega;
ALTER TABLE ONLY public.estadoentrega ALTER COLUMN idestadoentrega SET DEFAULT nextval('public.estadoentrega_idestadoentrega_seq'::regclass);
ALTER TABLE ONLY public.estadoentrega ADD CONSTRAINT estadoentrega_pkey PRIMARY KEY (idestadoentrega);
ALTER TABLE ONLY public.estadoentrega ADD CONSTRAINT estadoentrega_descripcionestadoentrega_key UNIQUE (descripcionestadoentrega);


-- Tabla: unidadmedida
CREATE TABLE public.unidadmedida (
    idunidad integer NOT NULL,
    nombreunidad character varying(50) NOT NULL,
    abreviatura character varying(10) NOT NULL
);

CREATE SEQUENCE public.unidadmedida_idunidad_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.unidadmedida_idunidad_seq OWNED BY public.unidadmedida.idunidad;
ALTER TABLE ONLY public.unidadmedida ALTER COLUMN idunidad SET DEFAULT nextval('public.unidadmedida_idunidad_seq'::regclass);
ALTER TABLE ONLY public.unidadmedida ADD CONSTRAINT unidadmedida_pkey PRIMARY KEY (idunidad);


-- Tabla: puntoentrega
CREATE TABLE public.puntoentrega (
    idpuntoentrega integer NOT NULL,
    nombrepunto character varying(100) NOT NULL,
    ubicacion text NOT NULL,
    descripcionpunto text
);

CREATE SEQUENCE public.puntoentrega_idpuntoentrega_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.puntoentrega_idpuntoentrega_seq OWNED BY public.puntoentrega.idpuntoentrega;
ALTER TABLE ONLY public.puntoentrega ALTER COLUMN idpuntoentrega SET DEFAULT nextval('public.puntoentrega_idpuntoentrega_seq'::regclass);
ALTER TABLE ONLY public.puntoentrega ADD CONSTRAINT puntoentrega_pkey PRIMARY KEY (idpuntoentrega);


---------------------------------------------------------------------
-- 2. TABLAS DEPENDIENTES DE PRIMER NIVEL
---------------------------------------------------------------------

-- Tabla: usuario
CREATE TABLE public.usuario (
    idusuario integer NOT NULL,
    dpiusuario character varying(20) NOT NULL,
    primernombre character varying(50) NOT NULL,
    segundonombre character varying(50),
    primerapellido character varying(50) NOT NULL,
    segundoapellido character varying(50),
    telefonousuario character varying(15) NOT NULL,
    email character varying(100) NOT NULL,
    contrasena character varying(255) NOT NULL,
    tipousuario integer NOT NULL,
    idestadousuario integer NOT NULL,
    fecharegistro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE public.usuario_idusuario_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.usuario_idusuario_seq OWNED BY public.usuario.idusuario;
ALTER TABLE ONLY public.usuario ALTER COLUMN idusuario SET DEFAULT nextval('public.usuario_idusuario_seq'::regclass);
ALTER TABLE ONLY public.usuario ADD CONSTRAINT usuario_pkey PRIMARY KEY (idusuario);
ALTER TABLE ONLY public.usuario ADD CONSTRAINT usuario_dpiusuario_key UNIQUE (dpiusuario);
ALTER TABLE ONLY public.usuario ADD CONSTRAINT usuario_email_key UNIQUE (email);


-- Tabla: producto
CREATE TABLE public.producto (
    idproducto integer NOT NULL,
    nombreproducto character varying(100) NOT NULL,
    descripcion text,
    precio numeric(10,2) NOT NULL,
    idunidadmedida integer NOT NULL,
    idproductor integer NOT NULL,
    activo boolean DEFAULT true,
    fecharegistro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    cantidaddisponible numeric(10,2) DEFAULT 0 NOT NULL
);

CREATE SEQUENCE public.producto_idproducto_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.producto_idproducto_seq OWNED BY public.producto.idproducto;
ALTER TABLE ONLY public.producto ALTER COLUMN idproducto SET DEFAULT nextval('public.producto_idproducto_seq'::regclass);
ALTER TABLE ONLY public.producto ADD CONSTRAINT producto_pkey PRIMARY KEY (idproducto);


-- Tabla: pedido
CREATE TABLE public.pedido (
    idpedido integer NOT NULL,
    idcliente integer NOT NULL,
    idproductor integer NOT NULL,
    fechasolicitud timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    idestadopedido integer NOT NULL
);

CREATE SEQUENCE public.pedido_idpedido_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.pedido_idpedido_seq OWNED BY public.pedido.idpedido;
ALTER TABLE ONLY public.pedido ALTER COLUMN idpedido SET DEFAULT nextval('public.pedido_idpedido_seq'::regclass);
ALTER TABLE ONLY public.pedido ADD CONSTRAINT pedido_pkey PRIMARY KEY (idpedido);


-- Tabla: reporte
CREATE TABLE public.reporte (
    idreporte integer NOT NULL,
    idemisor integer NOT NULL,
    idreceptor integer NOT NULL,
    comentarioreporte text NOT NULL,
    fechaenviorprt timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    estado character varying(20) DEFAULT 'pendiente'::character varying
);

CREATE SEQUENCE public.reporte_idreporte_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.reporte_idreporte_seq OWNED BY public.reporte.idreporte;
ALTER TABLE ONLY public.reporte ALTER COLUMN idreporte SET DEFAULT nextval('public.reporte_idreporte_seq'::regclass);
ALTER TABLE ONLY public.reporte ADD CONSTRAINT reporte_pkey PRIMARY KEY (idreporte);


---------------------------------------------------------------------
-- 3. TABLAS DEPENDIENTES DE SEGUNDO NIVEL / RELACIONES
---------------------------------------------------------------------

-- Tabla: acuerdo
CREATE TABLE public.acuerdo (
    idacuerdo integer NOT NULL,
    idpedido integer NOT NULL,
    precioacordado numeric(10,2) NOT NULL,
    cantidadacordada numeric(10,2) NOT NULL,
    fechaacordada timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    estadoacuerdo character varying(20) DEFAULT 'pendiente'::character varying,
    vigenciaacuerdo boolean DEFAULT true,
    idcreador integer,
    CONSTRAINT acuerdo_cantidadacordada_check CHECK ((cantidadacordada > (0)::numeric)),
    CONSTRAINT acuerdo_precioacordado_check CHECK ((precioacordado >= (0)::numeric))
);

CREATE SEQUENCE public.acuerdo_idacuerdo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.acuerdo_idacuerdo_seq OWNED BY public.acuerdo.idacuerdo;
ALTER TABLE ONLY public.acuerdo ALTER COLUMN idacuerdo SET DEFAULT nextval('public.acuerdo_idacuerdo_seq'::regclass);
ALTER TABLE ONLY public.acuerdo ADD CONSTRAINT acuerdo_pkey PRIMARY KEY (idacuerdo);


-- Tabla: calificacion
CREATE TABLE public.calificacion (
    idcalificacion integer NOT NULL,
    idpedido integer NOT NULL,
    idcalificador integer NOT NULL,
    idcalificado integer NOT NULL,
    puntaje integer NOT NULL,
    comentario text,
    fechacalificacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT calificacion_puntaje_check CHECK (((puntaje >= 1) AND (puntaje <= 5)))
);

CREATE SEQUENCE public.calificacion_idcalificacion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.calificacion_idcalificacion_seq OWNED BY public.calificacion.idcalificacion;
ALTER TABLE ONLY public.calificacion ALTER COLUMN idcalificacion SET DEFAULT nextval('public.calificacion_idcalificacion_seq'::regclass);
ALTER TABLE ONLY public.calificacion ADD CONSTRAINT calificacion_pkey PRIMARY KEY (idcalificacion);
ALTER TABLE ONLY public.calificacion ADD CONSTRAINT calificacion_idpedido_idcalificador_key UNIQUE (idpedido, idcalificador);


-- Tabla: entrega
CREATE TABLE public.entrega (
    identrega integer NOT NULL,
    idpedido integer NOT NULL,
    idpuntoentrega integer NOT NULL,
    fechaentrega timestamp without time zone,
    confirmadoproductor boolean DEFAULT false,
    confirmadocliente boolean DEFAULT false,
    idestadoentrega integer NOT NULL,
    fechaconfirmacionproductor timestamp without time zone,
    fechaconfirmacioncliente timestamp without time zone
);

CREATE SEQUENCE public.entrega_identrega_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.entrega_identrega_seq OWNED BY public.entrega.identrega;
ALTER TABLE ONLY public.entrega ALTER COLUMN identrega SET DEFAULT nextval('public.entrega_identrega_seq'::regclass);
ALTER TABLE ONLY public.entrega ADD CONSTRAINT entrega_pkey PRIMARY KEY (identrega);


-- Tabla: historialpedido
CREATE TABLE public.historialpedido (
    idhistorial integer NOT NULL,
    idpedido integer NOT NULL,
    estadohistorialpedido character varying(30) NOT NULL,
    fechacambio timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    comentario text
);

CREATE SEQUENCE public.historialpedido_idhistorial_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.historialpedido_idhistorial_seq OWNED BY public.historialpedido.idhistorial;
ALTER TABLE ONLY public.historialpedido ALTER COLUMN idhistorial SET DEFAULT nextval('public.historialpedido_idhistorial_seq'::regclass);
ALTER TABLE ONLY public.historialpedido ADD CONSTRAINT historialpedido_pkey PRIMARY KEY (idhistorial);


-- Tabla: mensaje
CREATE TABLE public.mensaje (
    idmensaje integer NOT NULL,
    idpedido integer NOT NULL,
    idemisor integer NOT NULL,
    idreceptor integer NOT NULL,
    contenidomsj text NOT NULL,
    fechaenviomsj timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    leido boolean DEFAULT false
);

CREATE SEQUENCE public.mensaje_idmensaje_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.mensaje_idmensaje_seq OWNED BY public.mensaje.idmensaje;
ALTER TABLE ONLY public.mensaje ALTER COLUMN idmensaje SET DEFAULT nextval('public.mensaje_idmensaje_seq'::regclass);
ALTER TABLE ONLY public.mensaje ADD CONSTRAINT mensaje_pkey PRIMARY KEY (idmensaje);


-- Tabla: productopedido
CREATE TABLE public.productopedido (
    idproductopedido integer NOT NULL,
    idpedido integer NOT NULL,
    idproducto integer NOT NULL,
    cantidad numeric(10,2) NOT NULL,
    preciounitario numeric(10,2) NOT NULL,
    CONSTRAINT productopedido_cantidad_check CHECK ((cantidad > (0)::numeric)),
    CONSTRAINT productopedido_preciounitario_check CHECK ((preciounitario >= (0)::numeric))
);

CREATE SEQUENCE public.productopedido_idproductopedido_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.productopedido_idproductopedido_seq OWNED BY public.productopedido.idproductopedido;
ALTER TABLE ONLY public.productopedido ALTER COLUMN idproductopedido SET DEFAULT nextval('public.productopedido_idproductopedido_seq'::regclass);
ALTER TABLE ONLY public.productopedido ADD CONSTRAINT productopedido_pkey PRIMARY KEY (idproductopedido);

---------------------------------------------------------------------
-- 4. RESTRICCIONES DE LLAVES FORÁNEAS (CONSTRAINTS)
---------------------------------------------------------------------

-- Llaves foráneas de 'usuario'
ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_tipousuario_fkey FOREIGN KEY (tipousuario) REFERENCES public.tipousuario(idtipousuario);
ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_idestadousuario_fkey FOREIGN KEY (idestadousuario) REFERENCES public.estadousuario(idestado);

-- Llaves foráneas de 'producto'
ALTER TABLE ONLY public.producto
    ADD CONSTRAINT producto_idunidadmedida_fkey FOREIGN KEY (idunidadmedida) REFERENCES public.unidadmedida(idunidad);
ALTER TABLE ONLY public.producto
    ADD CONSTRAINT producto_pkey PRIMARY KEY (idproducto);