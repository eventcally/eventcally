def test_index(client):
    response = client.get("/")
    assert b"eventcally" in response.data
