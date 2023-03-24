def test_index(client):
    response = client.get("/")
    assert b"EventCally" in response.data
