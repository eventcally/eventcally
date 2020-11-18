def test_create_for_admin_unit(client):
    response = client.get("/")
    assert b"oveda" in response.data
