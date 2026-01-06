-- Script para verificar y corregir permisos del usuario JefSerMat
-- Fecha: 2026-01-06
-- Problema: Usuario no puede ver requisiciones pendientes para aprobar

-- 1. VERIFICAR SI EL USUARIO TIENE EL ROL JefSerMat
SELECT 
    e.nombre,
    e.emailinstitucional,
    r.nomrol,
    er.actlaboralmente AS activo_laboral
FROM usuarios.empleados e
JOIN acceso.empleados_roles er ON er.emailinstitucional = e.emailinstitucional
JOIN acceso.roles r ON r.idrol = er.idrol
WHERE r.nomrol = 'JefSerMat'
ORDER BY e.nombre;

-- 2. VERIFICAR LA FUNCIÓN QUE LISTA REQUISICIONES PENDIENTES
-- Esta función debe existir y validar correctamente el rol
SELECT 
    p.proname AS nombre_funcion,
    pg_get_functiondef(p.oid) AS definicion
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'requisiciones'
  AND p.proname LIKE '%pendientes_jefe_materiales%';

-- 3. SI EL USUARIO EXISTE PERO NO TIENE ACTIVO EL ROL, ACTIVARLO
-- NOTA: Reemplazar 'email_del_usuario@ejemplo.com' con el email real
-- UPDATE acceso.empleados_roles
-- SET actlaboralmente = TRUE
-- WHERE emailinstitucional = 'email_del_usuario@ejemplo.com'
--   AND idrol = (SELECT idrol FROM acceso.roles WHERE nomrol = 'JefSerMat');

-- 4. SI EL ROL NO EXISTE PARA EL USUARIO, ASIGNARLO
-- NOTA: Reemplazar 'email_del_usuario@ejemplo.com' con el email real
-- INSERT INTO acceso.empleados_roles (emailinstitucional, idrol, actlaboralmente)
-- SELECT 
--     'email_del_usuario@ejemplo.com',
--     idrol,
--     TRUE
-- FROM acceso.roles
-- WHERE nomrol = 'JefSerMat'
-- ON CONFLICT (emailinstitucional, idrol) DO UPDATE
-- SET actlaboralmente = TRUE;

-- 5. VERIFICAR REQUISICIONES QUE DEBERÍAN ESTAR PENDIENTES
SELECT 
    r.codrequisicion,
    r.nomempleado,
    r.fecsolicitud,
    r.estgeneral,
    -- Estado de cada aprobador
    COALESCE(
        (SELECT EstadoAprobacion 
         FROM requisiciones.Aprobaciones a1 
         WHERE a1.IdRequisicion = r.IdRequisicion 
         AND a1.Rol = 'JefInmediato' 
         ORDER BY a1.FecAprobacion DESC LIMIT 1), 
        'Pendiente'
    ) as EstadoJefeInmediato,
    COALESCE(
        (SELECT EstadoAprobacion 
         FROM requisiciones.Aprobaciones a2 
         WHERE a2.IdRequisicion = r.IdRequisicion 
         AND a2.Rol = 'GerAdmon' 
         ORDER BY a2.FecAprobacion DESC LIMIT 1), 
        'Pendiente'
    ) as EstadoGerenteAdmin,
    COALESCE(
        (SELECT EstadoAprobacion 
         FROM requisiciones.Aprobaciones a3 
         WHERE a3.IdRequisicion = r.IdRequisicion 
         AND a3.Rol = 'JefSerMat' 
         ORDER BY a3.FecAprobacion DESC LIMIT 1), 
        'Pendiente'
    ) as EstadoJefeMateriales,
    COALESCE(
        (SELECT EstadoAprobacion 
         FROM requisiciones.Aprobaciones a4 
         WHERE a4.IdRequisicion = r.IdRequisicion 
         AND a4.Rol = 'EmpAlmacen' 
         ORDER BY a4.FecAprobacion DESC LIMIT 1), 
        'Pendiente'
    ) as EstadoAlmacen
FROM requisiciones.Requisiciones r
WHERE r.estgeneral NOT IN ('ENTREGADO', 'RECHAZADO', 'CANCELADO')
  -- Donde el Jefe Inmediato ya aprobó
  AND COALESCE(
        (SELECT EstadoAprobacion 
         FROM requisiciones.Aprobaciones a1 
         WHERE a1.IdRequisicion = r.IdRequisicion 
         AND a1.Rol = 'JefInmediato' 
         ORDER BY a1.FecAprobacion DESC LIMIT 1), 
        'Pendiente'
    ) = 'Aprobado'
  -- Y donde el Gerente Administrativo ya aprobó (o no es necesario)
  AND COALESCE(
        (SELECT EstadoAprobacion 
         FROM requisiciones.Aprobaciones a2 
         WHERE a2.IdRequisicion = r.IdRequisicion 
         AND a2.Rol = 'GerAdmon' 
         ORDER BY a2.FecAprobacion DESC LIMIT 1), 
        'Aprobado'  -- Si no hay registro, asumimos que no es necesario
    ) = 'Aprobado'
  -- Y donde el Jefe de Materiales aún NO ha aprobado
  AND COALESCE(
        (SELECT EstadoAprobacion 
         FROM requisiciones.Aprobaciones a3 
         WHERE a3.IdRequisicion = r.IdRequisicion 
         AND a3.Rol = 'JefSerMat' 
         ORDER BY a3.FecAprobacion DESC LIMIT 1), 
        'Pendiente'
    ) = 'Pendiente'
ORDER BY r.fecsolicitud DESC;

-- 6. CONSULTA DE DIAGNÓSTICO: VER TODOS LOS ROLES DEL SISTEMA
SELECT 
    r.idrol,
    r.nomrol,
    r.descripcion,
    COUNT(er.emailinstitucional) AS total_usuarios
FROM acceso.roles r
LEFT JOIN acceso.empleados_roles er ON er.idrol = r.idrol AND COALESCE(er.actlaboralmente, TRUE) = TRUE
GROUP BY r.idrol, r.nomrol, r.descripcion
ORDER BY r.nomrol;
