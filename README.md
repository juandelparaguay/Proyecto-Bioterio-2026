## Proyecto Bioterio 2026 - Enfoque predictivo

### Integrantes
- Juan Delvalle
- Fabrizio

### Tema
Nuestro tema es

### Titulo 

El titulo del proyecto es

### Tutor/a

- Profesora Romina

### Instalacion del servidor

## 1. Archivo de configuracion

1. Se tuvo tuvo que mover el archivo de configuracion ```.env``` dentro de la carpeta /composer para que encuentre al inicializar. 
2. Se modifico el archivo `settings.py` para incluir la direccion y las librerias que cargan el archivo de configuracion.
3. Se agrego la informacion de la base de datos local
4. Se ejecuto `python -c "import secrets; print(secrets.token_urlsafe(50))"` para crear un codigo secreto y pegarlo en SECRET_KEY

## Base de datos

1. Se creo la base de datos y el usuario
2. Se agrego los datos al archivo .env
3. Se ejecuta `python manage.py makemigrations`
4. Se ejecuta `python manage.py migrate`

## Ejecutar el servidor

1. Se ejecuta `python manage.py runserver`






### ERRORES ACTUALES

- Error al ejecutar el comando python manage.py makemigrations 
**ERROR:** 
```jango.db.utils.ProgrammingError: relation protocolos_procedimientobase does not exist LINE 1: SELECT COUNT(*) AS __count FROM protocolos_procedimientob```

**SOLUCION:*** Eliminar el bloque de codigo que da el error. En forms.py, intenta consultar una tabla que aun no esta creada para buscar la cantidad de protocolos.