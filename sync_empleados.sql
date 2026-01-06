INSERT INTO usuarios.empleados (emailinstitucional, nombre, iddependencia, dni, dnijefeinmediato, creadoen, creadopor, actualizadoen, actualizadopor)
VALUES
('luis.cardona@sedh.gob.hn','LUIS ENRIQUE CARDONA CASTRO','fcf6b2e0-91d2-463a-a280-8b1bdfd260a3','0801199710100','0801199306721','2025-09-04','SQLServer',NULL,NULL),
('emerson.duron@sedh.gob.hn','EMERSON EDILBERTO DURON VILLALTA','fcf6b2e0-91d2-463a-a280-8b1bdfd260a3','0801199306721','0703199100458','2025-09-04','SQLServer',NULL,NULL),
('escarleth.ortiz@sedh.gob.hn','ESCARLETH YADIRA NUÑEZ ORTIZ','eb0ffefd-5036-4f4c-ae99-2dd323401bb6','0801199510174','0703199100458','2025-09-04','SQLServer',NULL,NULL),
('admin@test.com','Administrador del Sistema',NULL,'00000000000',NULL,NULL,NULL,NULL,NULL),
('juan.gabriel@sedh.gob.hn','JUAN GABRIEL','68b3fe1c-1bd2-4542-9248-a0fa5f6fdbda','0801199710102','0703199100458','2025-11-19','humberto.zelaya@sedh.gob.hn',NULL,NULL),
('Ruedas.G@sedh.gob.hn','RUEDAS','68b3fe1c-1bd2-4542-9248-a0fa5f6fdbda','0801199710145','0703199100458','2025-11-19','humberto.zelaya@sedh.gob.hn',NULL,NULL),
('pablo.maldonado@sedh.gob.hn','PABLO MALDONADO','68b3fe1c-1bd2-4542-9248-a0fa5f6fdbda','0801199710147','0801199710145','2025-11-19','humberto.zelaya@sedh.gob.hn',NULL,NULL),
('tu.email@dominio.com','Tu Nombre',NULL,NULL,NULL,NULL,NULL,NULL,NULL),
('luis.rosales@sedh.gob.hn','LUIS FRANCISCO ROSALES PALMA','542b0a6b-ee35-43d5-a3c1-e078a813a49f','0703199100458','0703199100458','2025-09-04','SQLServer',NULL,NULL),
('allan.alfaro@sedh.gob.hn','ALLAN ERNESTO ALFARO MOLINA','5dda2518-c6e1-4653-bd3a-928c87bdf980','0801198716345','0703199100458','2025-09-04','SQLServer',NULL,NULL),
('alejandro.rodriguez@sedh.gob.hn','JOSE ALEJANDRO RODRIGUEZ MADRID','14747aa4-0983-497b-ac65-543a8887db58','0801199311188','0703199100458','2025-09-04','SQLServer',NULL,NULL),
('humberto.zelaya@sedh.gob.hn','Humberto Josue Zelaya Lagos','fcf6b2e0-91d2-463a-a280-8b1bdfd260a3','0801199311188','0801199306721','2025-10-13','SQLServer',NULL,NULL)
ON CONFLICT (emailinstitucional) DO UPDATE SET
  nombre = EXCLUDED.nombre,
  iddependencia = EXCLUDED.iddependencia,
  dni = EXCLUDED.dni,
  dnijefeinmediato = EXCLUDED.dnijefeinmediato,
  actualizadopor = COALESCE(EXCLUDED.actualizadopor, 'sync_empleados.sql'),
  actualizadoen = NOW();