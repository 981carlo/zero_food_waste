# Zero Food Waste - Despliegue con Docker

## 1. Descripción del proyecto

El proyecto está preparado para ejecutarse en contenedores Docker usando **Django**, **Uvicorn**, **Nginx** y **MongoDB**.

## 2. Tecnologías utilizadas

- Python 3.14
- Django 6
- Django MongoDB Backend
- MongoDB
- Uvicorn
- Nginx
- Docker
- Docker Compose

## 3. Variables de entorno

Antes de ejecutar el proyecto, crear un archivo `.env` en la raíz del proyecto a partir de `.env.example`.

Contenido recomendado para desarrollo con Docker Compose:

```env
MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=zero_food_waste
```

Dentro de Docker Compose, el nombre `mongo` hace referencia al servicio de MongoDB definido en `docker-compose.yml`.

## 4. Construcción y ejecución con Docker Compose

Para levantar el proyecto completo, ejecutar desde la raíz del proyecto:

```bash
docker compose up --build
```

Este comando construye la imagen de Django/Uvicorn, descarga la imagen de MongoDB si no existe, construye la imagen de Nginx y levanta los contenedores necesarios.

El sistema queda formado por tres contenedores:

- `mongo`: base de datos MongoDB.
- `web`: aplicación Django ejecutada mediante Uvicorn.
- `nginx`: servidor Nginx que recibe las peticiones HTTP y las redirige a Django.

## 5. Flujo de funcionamiento de la aplicación

1. El usuario accede desde el navegador a `http://localhost:8080`.
2. La petición llega al contenedor de Nginx.
3. Nginx actúa como proxy inverso y reenvía la petición al servicio `web` en el puerto `8000`.
4. El servicio `web` ejecuta Django mediante Uvicorn usando la aplicación ASGI definida en `config/asgi.py`.
5. Django procesa la petición, aplica su configuración, rutas y lógica interna.
6. Si la aplicación necesita acceder a datos, Django se comunica con MongoDB mediante la URI configurada en `MONGO_URI`.
7. MongoDB devuelve los datos a Django.
8. Django genera la respuesta.
9. Uvicorn devuelve la respuesta a Nginx.
10. Nginx devuelve la respuesta final al navegador.

Flujo resumido:

```text
Navegador → Nginx → Uvicorn/Django → MongoDB
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
http://localhost:8080/admin/
```

## 8. Parar los contenedores

Para detener los contenedores sin borrar los datos persistentes:

```bash
docker compose down
```

Para detener los contenedores y borrar también los datos almacenados en MongoDB:

```bash
docker compose down -v
```

## 9. Construcción solo con Dockerfile

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
docker run -d --name zero_food_waste_app_run --network zero_food_waste_net -p 8001:8000 -e MONGO_URI=mongodb://zero_food_waste_mongo_run:27017 -e MONGO_DB_NAME=zero_food_waste zero_food_waste
```

La aplicación quedaría disponible en:

```text
http://localhost:8001
```

Este modo comprueba que la imagen creada con el Dockerfile puede ejecutarse con `docker run -d`. Para levantar el sistema completo con Nginx, Django/Uvicorn y MongoDB, se recomienda usar:

```bash
docker compose up --build
```
