import pytest
from django.test import Client

@pytest.mark.django_db
def test_hello_world():
    client = Client()
    response = client.get("/hello_world/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello world from Django"}
