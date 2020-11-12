import pytest

def test_index(client):
    response = client.get('/')
    assert b'oveda' in response.data