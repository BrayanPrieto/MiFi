-- =============================================================================
-- MiFi (Mis Finanzas) - Schema Principal
-- Compatible con: PostgreSQL (Neon / Supabase / Local)
-- Versión: 1.0.0
-- =============================================================================

-- Habilitar extensión para UUIDs y encriptación
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- SECCIÓN 1: USUARIOS Y AUTENTICACIÓN
-- =============================================================================

CREATE TABLE usuarios (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre        VARCHAR(100) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,                         -- bcrypt hash, NUNCA texto plano
    avatar_url    TEXT,
    moneda        CHAR(3) NOT NULL DEFAULT 'COP',        -- ISO 4217: COP, USD, EUR...
    activo        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  usuarios              IS 'Usuarios de la aplicación. Cada usuario tiene sus propios datos financieros aislados.';
COMMENT ON COLUMN usuarios.password_hash IS 'Hash bcrypt generado por la capa de aplicación (FastAPI / passlib). Nunca almacenar texto plano.';
COMMENT ON COLUMN usuarios.moneda       IS 'Moneda base del usuario. Código ISO 4217.';


-- =============================================================================
-- SECCIÓN 2: ENUMERACIONES (TIPOS)
-- =============================================================================

CREATE TYPE tipo_transaccion AS ENUM (
    'INGRESO',
    'GASTO_FIJO',
    'GASTO_VARIABLE',
    'PRESTAMO_CUOTA',   -- Pago de cuota de un préstamo/deuda
    'AHORRO'
);

CREATE TYPE tipo_cuenta AS ENUM (
    'EFECTIVO',
    'CUENTA_AHORROS',
    'CUENTA_CORRIENTE',
    'TARJETA_CREDITO',
    'BILLETERA_DIGITAL',  -- Nequi, Daviplata, etc.
    'OTRO'
);

CREATE TYPE estado_prestamo AS ENUM (
    'ACTIVO',
    'PAGADO',
    'EN_MORA'
);

CREATE TYPE tipo_prestamo AS ENUM (
    'BANCO',        -- Crédito bancario formal
    'TERCERO'       -- Deuda con persona natural
);


-- =============================================================================
-- SECCIÓN 3: CUENTAS / BILLETERAS
-- =============================================================================

CREATE TABLE cuentas (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id  UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre      VARCHAR(100) NOT NULL,
    tipo        tipo_cuenta NOT NULL DEFAULT 'CUENTA_AHORROS',
    saldo       NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    color       CHAR(7),                                 -- Hex color para la UI (#RRGGBB)
    icono       VARCHAR(50),                             -- Nombre de ícono PrimeIcons
    es_principal BOOLEAN NOT NULL DEFAULT FALSE,         -- Cuenta principal del usuario
    activa      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  cuentas            IS 'Cuentas o billeteras del usuario. Ej: Nómina Bancolombia, Nequi, Efectivo.';
COMMENT ON COLUMN cuentas.saldo      IS 'Saldo actual calculado. Se actualiza mediante trigger en cada transacción.';
COMMENT ON COLUMN cuentas.es_principal IS 'Si TRUE, es la cuenta por defecto al registrar transacciones.';

-- Un usuario no puede tener dos cuentas con el mismo nombre
CREATE UNIQUE INDEX uq_cuentas_usuario_nombre ON cuentas(usuario_id, nombre) WHERE activa = TRUE;


-- =============================================================================
-- SECCIÓN 4: CATEGORÍAS
-- =============================================================================

CREATE TABLE categorias (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id  UUID REFERENCES usuarios(id) ON DELETE CASCADE,  -- NULL = categoría global/predeterminada
    nombre      VARCHAR(100) NOT NULL,
    tipo        tipo_transaccion NOT NULL,
    color       CHAR(7),
    icono       VARCHAR(50),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  categorias           IS 'Categorías de transacciones. usuario_id = NULL indica categoría global del sistema.';
COMMENT ON COLUMN categorias.usuario_id IS 'Si es NULL, la categoría es predeterminada y visible para todos los usuarios.';

-- Índice para búsquedas frecuentes por usuario y tipo
CREATE INDEX idx_categorias_usuario_tipo ON categorias(usuario_id, tipo);

-- Categorías predeterminadas del sistema (usuario_id = NULL)
INSERT INTO categorias (nombre, tipo) VALUES
    -- Ingresos
    ('Salario / Nómina',        'INGRESO'),
    ('Bono',                    'INGRESO'),
    ('Auxilio',                 'INGRESO'),
    ('Ingreso Extra',           'INGRESO'),
    ('Dividendos / Inversión',  'INGRESO'),
    -- Gastos Fijos
    ('Transporte',              'GASTO_FIJO'),
    ('Arriendo / Vivienda',     'GASTO_FIJO'),
    ('Servicios Públicos',      'GASTO_FIJO'),
    ('Suscripción Digital',     'GASTO_FIJO'),   -- Netflix, GPT, Prime...
    ('Aporte al Hogar',         'GASTO_FIJO'),
    ('Plan de Teléfono',        'GASTO_FIJO'),
    ('Seguro',                  'GASTO_FIJO'),
    -- Gastos Variables
    ('Mercado / Alimentos',     'GASTO_VARIABLE'),
    ('Salidas / Ocio',          'GASTO_VARIABLE'),
    ('Ropa / Accesorios',       'GASTO_VARIABLE'),
    ('Salud / Farmacia',        'GASTO_VARIABLE'),
    ('Educación',               'GASTO_VARIABLE'),
    ('Compras Esporádicas',     'GASTO_VARIABLE'),
    -- Préstamos
    ('Cuota Préstamo Banco',    'PRESTAMO_CUOTA'),
    ('Cuota Deuda Tercero',     'PRESTAMO_CUOTA'),
    -- Ahorro
    ('Ahorro Mensual',          'AHORRO'),
    ('Meta de Ahorro',          'AHORRO');


-- =============================================================================
-- SECCIÓN 5: PRÉSTAMOS Y DEUDAS
-- =============================================================================

CREATE TABLE prestamos (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id              UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    entidad                 VARCHAR(150) NOT NULL,           -- Ej: 'Banco de Bogotá', 'Elba', 'Yudy'
    tipo                    tipo_prestamo NOT NULL DEFAULT 'BANCO',
    descripcion             TEXT,
    monto_total             NUMERIC(15, 2) NOT NULL,
    saldo_pendiente         NUMERIC(15, 2) NOT NULL,
    cuota_mensual_esperada  NUMERIC(15, 2) NOT NULL,         -- Cuota "Requerida"
    tasa_interes_mensual    NUMERIC(6, 4),                  -- % mensual, ej: 1.5 = 1.5%
    dia_pago                SMALLINT CHECK (dia_pago BETWEEN 1 AND 31), -- Día del mes esperado
    estado                  estado_prestamo NOT NULL DEFAULT 'ACTIVO',
    fecha_inicio            DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_fin_esperada      DATE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  prestamos                      IS 'Préstamos y deudas del usuario, tanto bancarios como con terceros.';
COMMENT ON COLUMN prestamos.saldo_pendiente      IS 'Se recalcula automáticamente al registrar pagos de cuota.';
COMMENT ON COLUMN prestamos.cuota_mensual_esperada IS 'Equivalente a la columna "Requerido" de tu Excel.';
COMMENT ON COLUMN prestamos.dia_pago             IS 'Día del mes en que vence la cuota. Usado para alertas.';

CREATE INDEX idx_prestamos_usuario_estado ON prestamos(usuario_id, estado);


-- =============================================================================
-- SECCIÓN 6: PRESUPUESTOS MENSUALES (METAS DE GASTO)
-- =============================================================================

CREATE TABLE presupuestos (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id   UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    categoria_id UUID NOT NULL REFERENCES categorias(id) ON DELETE CASCADE,
    mes          SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    anio         SMALLINT NOT NULL CHECK (anio >= 2020),
    monto_limite NUMERIC(15, 2) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (usuario_id, categoria_id, mes, anio)
);

COMMENT ON TABLE presupuestos IS 'Límites de gasto por categoría y mes. Permite comparar presupuestado vs. ejecutado.';


-- =============================================================================
-- SECCIÓN 7: METAS DE AHORRO
-- =============================================================================

CREATE TABLE metas_ahorro (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id      UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre          VARCHAR(150) NOT NULL,               -- Ej: 'Viaje a Europa', 'Fondo de Emergencia'
    monto_objetivo  NUMERIC(15, 2) NOT NULL,
    monto_actual    NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    porcentaje_meta NUMERIC(5, 2),                       -- Ej: 10 = guardar el 10% del ingreso del mes
    fecha_objetivo  DATE,
    completada      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  metas_ahorro          IS 'Metas de ahorro del usuario con seguimiento de progreso.';
COMMENT ON COLUMN metas_ahorro.porcentaje_meta IS 'Porcentaje de los ingresos mensuales a destinar a esta meta.';


-- =============================================================================
-- SECCIÓN 8: TRANSACCIONES (CORAZÓN DE LA APP)
-- =============================================================================

CREATE TABLE transacciones (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id     UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    cuenta_id      UUID NOT NULL REFERENCES cuentas(id),
    categoria_id   UUID REFERENCES categorias(id),
    prestamo_id    UUID REFERENCES prestamos(id),         -- Solo si es pago de cuota
    meta_ahorro_id UUID REFERENCES metas_ahorro(id),      -- Solo si es movimiento de ahorro
    tipo           tipo_transaccion NOT NULL,
    monto          NUMERIC(15, 2) NOT NULL CHECK (monto > 0),
    fecha          DATE NOT NULL DEFAULT CURRENT_DATE,
    descripcion    VARCHAR(500),
    es_requerido   BOOLEAN NOT NULL DEFAULT TRUE,         -- "Requerido" de tu Excel
    esta_pagado    BOOLEAN NOT NULL DEFAULT FALSE,        -- "Pagado" de tu Excel
    fuente_ia      BOOLEAN NOT NULL DEFAULT FALSE,        -- TRUE si fue ingresado por IA/lenguaje natural
    texto_original TEXT,                                  -- Texto original si fuente_ia = TRUE (ej: "Gasté 50k en gasolina")
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  transacciones             IS 'Registro de todos los movimientos de dinero. Núcleo de la aplicación.';
COMMENT ON COLUMN transacciones.es_requerido IS 'TRUE = gasto obligatorio/planeado. FALSE = gasto opcional.';
COMMENT ON COLUMN transacciones.esta_pagado  IS 'TRUE = ya se realizó el pago efectivo.';
COMMENT ON COLUMN transacciones.fuente_ia    IS 'TRUE si la transacción fue creada por el motor de IA (Ollama).';
COMMENT ON COLUMN transacciones.texto_original IS 'El texto en lenguaje natural original, para auditoría del modelo de IA.';

-- Índices para los filtros más comunes (dashboard, reportes)
CREATE INDEX idx_transacciones_usuario_fecha   ON transacciones(usuario_id, fecha DESC);
CREATE INDEX idx_transacciones_usuario_tipo    ON transacciones(usuario_id, tipo);
CREATE INDEX idx_transacciones_cuenta          ON transacciones(cuenta_id);
CREATE INDEX idx_transacciones_categoria       ON transacciones(categoria_id);
CREATE INDEX idx_transacciones_mes_anio        ON transacciones(usuario_id, EXTRACT(YEAR FROM fecha), EXTRACT(MONTH FROM fecha));


-- =============================================================================
-- SECCIÓN 9: TRIGGERS (AUTOMATIZACIÓN)
-- =============================================================================

-- Función genérica para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger updated_at a todas las tablas que lo necesitan
CREATE TRIGGER trg_usuarios_updated_at     BEFORE UPDATE ON usuarios     FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_cuentas_updated_at      BEFORE UPDATE ON cuentas      FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_prestamos_updated_at    BEFORE UPDATE ON prestamos    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_metas_ahorro_updated_at BEFORE UPDATE ON metas_ahorro FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_transacciones_updated_at BEFORE UPDATE ON transacciones FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- Función: actualizar saldo de cuenta al insertar/eliminar/actualizar una transacción
CREATE OR REPLACE FUNCTION fn_actualizar_saldo_cuenta()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.tipo = 'INGRESO' THEN
            UPDATE cuentas SET saldo = saldo + NEW.monto WHERE id = NEW.cuenta_id;
        ELSE
            UPDATE cuentas SET saldo = saldo - NEW.monto WHERE id = NEW.cuenta_id;
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.tipo = 'INGRESO' THEN
            UPDATE cuentas SET saldo = saldo - OLD.monto WHERE id = OLD.cuenta_id;
        ELSE
            UPDATE cuentas SET saldo = saldo + OLD.monto WHERE id = OLD.cuenta_id;
        END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        -- Revertir el efecto del monto anterior
        IF OLD.tipo = 'INGRESO' THEN
            UPDATE cuentas SET saldo = saldo - OLD.monto WHERE id = OLD.cuenta_id;
        ELSE
            UPDATE cuentas SET saldo = saldo + OLD.monto WHERE id = OLD.cuenta_id;
        END IF;
        -- Aplicar el efecto del nuevo monto
        IF NEW.tipo = 'INGRESO' THEN
            UPDATE cuentas SET saldo = saldo + NEW.monto WHERE id = NEW.cuenta_id;
        ELSE
            UPDATE cuentas SET saldo = saldo - NEW.monto WHERE id = NEW.cuenta_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_transaccion_saldo
    AFTER INSERT OR UPDATE OR DELETE ON transacciones
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_saldo_cuenta();

-- Función: actualizar saldo_pendiente de préstamo al registrar un pago de cuota
CREATE OR REPLACE FUNCTION fn_actualizar_saldo_prestamo()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.prestamo_id IS NOT NULL AND NEW.tipo = 'PRESTAMO_CUOTA' THEN
        UPDATE prestamos
        SET saldo_pendiente = GREATEST(0, saldo_pendiente - NEW.monto)
        WHERE id = NEW.prestamo_id;
        -- Marcar como pagado si el saldo llega a 0
        UPDATE prestamos SET estado = 'PAGADO' WHERE id = NEW.prestamo_id AND saldo_pendiente = 0;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_pago_prestamo_saldo
    AFTER INSERT ON transacciones
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_saldo_prestamo();


-- =============================================================================
-- SECCIÓN 10: VISTAS ÚTILES PARA LA APP
-- =============================================================================

-- Vista: resumen mensual de ingresos y gastos por usuario
CREATE OR REPLACE VIEW v_resumen_mensual AS
SELECT
    usuario_id,
    EXTRACT(YEAR  FROM fecha)::INT AS anio,
    EXTRACT(MONTH FROM fecha)::INT AS mes,
    SUM(CASE WHEN tipo = 'INGRESO'         THEN monto ELSE 0 END) AS total_ingresos,
    SUM(CASE WHEN tipo = 'GASTO_FIJO'      THEN monto ELSE 0 END) AS total_gastos_fijos,
    SUM(CASE WHEN tipo = 'GASTO_VARIABLE'  THEN monto ELSE 0 END) AS total_gastos_variables,
    SUM(CASE WHEN tipo = 'PRESTAMO_CUOTA'  THEN monto ELSE 0 END) AS total_cuotas_prestamos,
    SUM(CASE WHEN tipo = 'AHORRO'          THEN monto ELSE 0 END) AS total_ahorros,
    SUM(CASE WHEN tipo != 'INGRESO'        THEN monto ELSE 0 END) AS total_egresos,
    SUM(CASE WHEN tipo = 'INGRESO' THEN monto ELSE -monto END)    AS balance_neto
FROM transacciones
WHERE esta_pagado = TRUE
GROUP BY usuario_id, anio, mes;

COMMENT ON VIEW v_resumen_mensual IS 'Resumen financiero mensual por usuario. Solo incluye transacciones ya pagadas.';

-- Vista: estado de préstamos activos con progreso de pago
CREATE OR REPLACE VIEW v_prestamos_activos AS
SELECT
    p.id,
    p.usuario_id,
    p.entidad,
    p.tipo,
    p.monto_total,
    p.saldo_pendiente,
    p.cuota_mensual_esperada,
    p.dia_pago,
    p.estado,
    ROUND((1 - p.saldo_pendiente / NULLIF(p.monto_total, 0)) * 100, 2) AS porcentaje_pagado,
    COALESCE(SUM(t.monto), 0)                                           AS total_pagado_real
FROM prestamos p
LEFT JOIN transacciones t ON t.prestamo_id = p.id AND t.esta_pagado = TRUE
WHERE p.estado = 'ACTIVO'
GROUP BY p.id;

COMMENT ON VIEW v_prestamos_activos IS 'Resumen de préstamos activos con porcentaje de avance y total pagado real.';

-- Vista: gastos por categoría en el mes actual
CREATE OR REPLACE VIEW v_gastos_mes_actual AS
SELECT
    t.usuario_id,
    c.nombre AS categoria,
    c.tipo,
    SUM(t.monto) AS total_gastado,
    COUNT(*)     AS num_transacciones
FROM transacciones t
JOIN categorias c ON c.id = t.categoria_id
WHERE
    t.tipo IN ('GASTO_FIJO', 'GASTO_VARIABLE', 'PRESTAMO_CUOTA')
    AND EXTRACT(YEAR  FROM t.fecha) = EXTRACT(YEAR  FROM CURRENT_DATE)
    AND EXTRACT(MONTH FROM t.fecha) = EXTRACT(MONTH FROM CURRENT_DATE)
GROUP BY t.usuario_id, c.nombre, c.tipo;

COMMENT ON VIEW v_gastos_mes_actual IS 'Gastos agrupados por categoría para el mes en curso, útil para el dashboard.';
