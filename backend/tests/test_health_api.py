def test_health_check_api(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "DigiBills API"


def test_database_health_check_api(client):
    response = client.get("/health/database")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["result"] == 1
