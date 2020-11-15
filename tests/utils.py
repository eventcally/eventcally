import re
from flask import g


class UtilActions(object):
    def __init__(self, client):
        self._client = client

    def register(self, email="test@test.de", password="MeinPasswortIstDasBeste"):
        response = self._client.get("/register")
        assert response.status_code == 200

        with self._client:
            response = self._client.post(
                "/register",
                data={
                    "email": email,
                    "password": password,
                    "password_confirm": password,
                    "csrf_token": self.get_csrf(response),
                    "submit": "Register",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert g.identity.user.email == email

    def login(self, email="test@test.de", password="MeinPasswortIstDasBeste"):
        response = self._client.get("/login")
        assert response.status_code == 200

        with self._client:
            response = self._client.post(
                "/login",
                data={
                    "email": email,
                    "password": password,
                    "csrf_token": self.get_csrf(response),
                    "submit": "Anmelden",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert g.identity.user.email == email

    def logout(self):
        return self._client.get("/logout")

    def get_csrf(self, response, prefix=None):
        name = "csrf_token"
        if prefix:
            name = prefix + "-" + name

        pattern = (
            '<input id="' + name + '" name="' + name + '" type="hidden" value="(.*)">'
        )
        return (
            re.search(pattern.encode("utf-8"), response.data).group(1).decode("utf-8")
        )
