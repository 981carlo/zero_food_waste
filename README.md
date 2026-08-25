# Zero Food Waste

## 1. Descripción del proyecto

Zero Food Waste es una aplicación web orientada a reducir el desperdicio alimentario doméstico mediante la gestión de alimentos disponibles en el hogar y la generación de recetas personalizadas.

La aplicación permite al usuario registrar alimentos en una despensa personal, controlar sus fechas de caducidad, consultar los productos próximos a caducar y generar recetas mediante un modelo de lenguaje integrado a través de la API de Gemini.

El proyecto está preparado para ejecutarse en contenedores Docker usando Django, Uvicorn, Nginx y MongoDB.

## 2. Funcionalidades principales

- Registro de usuarios.
- Inicio y cierre de sesión.
- Gestión de alimentos por usuario.
- Creación, consulta, edición y eliminación de alimentos.
- Asociación de cada alimento al usuario autenticado.
- Consulta de alimentos próximos a caducar.
- Generación de recetas mediante la API de Gemini.
- Selección opcional de alimentos para generar recetas.
- Modificación de recetas generadas mediante indicaciones del usuario.
- Gestión de errores durante la llamada al LLM.
- Gestión de errores en formularios y accesos no válidos.
- Caducidad de sesión por inactividad.

## 3. Tecnologías utilizadas

- Python 3.14
- Django 6
- Django REST Framework
- Django MongoDB Backend
- MongoDB
- Gemini API
- Uvicorn
- Nginx
- Docker
- Docker Compose

## 4. Variables de entorno

Antes de ejecutar el proyecto, crear un archivo `.env` en la raíz del proyecto a partir de `.env.example`.

Contenido recomendado para desarrollo con Docker Compose:

```env
SECRET_KEY=change-me
DEBUG=True
MONGO_URI=mongodb://mongo:27017/
MONGO_DB_NAME=zero_food_waste
GEMINI_API_KEY=change-me
GEMINI_MODEL=gemini-3.6-flash
```

## 5. Construcción y ejecución con Docker Compose

Para levantar el proyecto completo, ejecutar desde la raíz del proyecto:

```bash
docker compose up --build
```

Este comando construye la imagen de Django/Uvicorn, descarga la imagen de MongoDB si no existe, construye la imagen de Nginx y levanta los contenedores necesarios.

El sistema queda formado por tres contenedores:

- `mongo`: base de datos MongoDB.
- `web`: aplicación Django ejecutada mediante Uvicorn.
- `nginx`: servidor Nginx que recibe las peticiones HTTP y las redirige a Django.

La aplicación queda disponible en:

```text
http://localhost
```

## 6. Migraciones

Con los contenedores levantados, se pueden ejecutar las migraciones con:

```bash
docker compose exec web python manage.py migrate
```

Este comando ejecuta las migraciones dentro del contenedor `web`, usando la conexión a MongoDB definida en las variables de entorno.

## 7. Crear un superusuario

Para crear un usuario administrador de Django:

```bash
docker compose exec web python manage.py createsuperuser
```

Después, el panel de administración estará disponible en:

```text
http://localhost/admin/
```

## 8. Comprobación del proyecto

Para comprobar que la configuración de Django no presenta errores:

```bash
docker compose exec web python manage.py check
```

## 9. Parar los contenedores

Para detener los contenedores sin borrar los datos persistentes:

```bash
docker compose down
```

Para detener los contenedores y borrar también los datos almacenados en MongoDB:

```bash
docker compose down -v
```

## 10. Construcción solo con Dockerfile

También se puede construir la imagen principal del proyecto con:

```bash
docker build -t zero_food_waste .
```

Para ejecutarla con `docker run -d`, Django necesita acceder a MongoDB. Por eso, si no se usa Docker Compose, hay que crear una red compartida y levantar MongoDB manualmente:

```bash
docker network create zero_food_waste_net
```

```bash
docker run -d --name zero_food_waste_mongo_run --network zero_food_waste_net -p 27017:27017 -v zero_food_waste_mongo_data:/data/db mongo:8.0
```

```bash
docker run -d --name zero_food_waste_app_run --network zero_food_waste_net -p 8001:8000 -e MONGO_URI=mongodb://zero_food_waste_mongo_run:27017/ -e MONGO_DB_NAME=zero_food_waste zero_food_waste
```

La aplicación quedaría disponible en:

```text
http://localhost:8001
```

Este modo comprueba que la imagen creada con el Dockerfile puede ejecutarse con `docker run -d`. Para levantar el sistema completo con Nginx, Django/Uvicorn y MongoDB, se recomienda usar:

```bash
docker compose up --build
```

## 11. Rutas principales

### Aplicación web

```text
/                              Página de inicio
/usuarios/registro-web/        Registro de usuario
/usuarios/login-web/           Inicio de sesión
/usuarios/logout-web/          Cierre de sesión
/despensa/alimentos/           Listado de alimentos
/despensa/alimentos/nuevo/     Alta de alimento
/despensa/alimentos/proximos/  Alimentos próximos a caducar
/despensa/recetas/generar/     Generación de recetas
/admin/                        Panel de administración de Django
```

### API

```text
/api/alimentos/                 Endpoint de alimentos
/api/alimentos/proximos/        Endpoint de alimentos próximos a caducar
```

## 12. Flujo de funcionamiento

El flujo general de la aplicación con Docker Compose es el siguiente:

```text
Petición:
Navegador → Nginx → Uvicorn/Django → MongoDB

Respuesta:
MongoDB → Uvicorn/Django → Nginx → Navegador
```

1. El usuario accede desde el navegador a `http://localhost`.
2. La petición llega al contenedor de Nginx.
3. Nginx actúa como proxy inverso y reenvía la petición al servicio `web`.
4. El servicio `web` ejecuta Django mediante Uvicorn.
5. Django procesa la petición, aplica las rutas y ejecuta la lógica correspondiente.
6. Si la aplicación necesita acceder a datos, Django se comunica con MongoDB.
7. Django genera la respuesta y la devuelve al navegador a través de Uvicorn y Nginx.
