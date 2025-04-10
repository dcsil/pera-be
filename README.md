### How to run
    $ pip install django
    $ python manage.py runserver
See [pera\_be/urls.py](pera_be/urls.py).

### Running with Docker

You can run the backend using **Docker** with the following commands.

### Build the Image
Run this in the project root:

```shell
docker build -t pera-backend .
```

### Run the Container

```shell
docker run -e SPEECH_KEY='dummy_test_key' -e SPEECH_REGION='dummy_test_region' -p 8000:8000 pera-backend
```

Now, the app should be running at http://127.0.0.1:8000

### Running Backend + Postgres with Docker Compose
To spin up both the Django app and a local Postgres DB together:

```shell
docker compose up --build
```
This runs:
- **web**: your Django backend (on port 8000)
- **db**: Postgres 15 database (on port 5432)

Make sure you have a .env file in the root folder that looks like this:

```env
SPEECH_KEY=our_azure_speech_key
SPEECH_REGION=our_azure_region
DB_NAME=pera_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
DB_SSL_MODE=disable
```

First-time Setup (after running compose)

If you're making new models or updating existing ones:

```shell
docker compose exec web python manage.py makemigrations
```

Run migrations inside the web container:

```shell
docker compose exec web python manage.py migrate
```

That sets up the DB tables and you're good to go!

## Running Tests in Docker

### To run the backend tests inside Docker:

```shell
docker run --rm pera-backend pytest
```

### Debugging & Logs
Check container logs:

```shell
docker logs <container_id>
```

### Jump into the running container:

```shell
docker exec -it <container_id> sh
```
