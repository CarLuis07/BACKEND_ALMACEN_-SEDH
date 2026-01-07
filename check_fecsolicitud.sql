-- Ver tipo de fecsolicitud
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema='requisiciones' 
AND table_name='requisiciones' 
AND column_name='fecsolicitud';
