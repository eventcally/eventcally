import re
from flask import g
from sqlalchemy.exc import IntegrityError


class UtilActions(object):
    def __init__(self, client, app):
        self._client = client
        self._app = app

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
        from project.services.user import find_user_by_email

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

        with self._app.app_context():
            user = find_user_by_email(email)
            user_id = user.id

        return user_id

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

    def mock_db_commit(self, mocker):
        mocked_commit = mocker.patch("project.db.session.commit")
        mocked_commit.side_effect = IntegrityError(
            "MockException", "MockException", None
        )

    def mock_send_mails(self, mocker):
        return mocker.patch("project.views.utils.send_mails")

    def assert_send_mail_called(self, mock, recipient):
        mock.assert_called_once()
        args, kwargs = mock.call_args
        assert args[0] == [recipient]
