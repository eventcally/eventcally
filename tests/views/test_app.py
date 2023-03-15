def test_index(client):
    response = client.get("/")
    assert b"gsevpt" in response.data
