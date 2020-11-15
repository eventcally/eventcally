def test_events(client):
    response = client.get("/api/events")
    assert response.status_code == 200
