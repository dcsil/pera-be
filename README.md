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
docker run -p 8000:8000 pera-backend
```

Now, the app should be running at http://127.0.0.1:8000

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
