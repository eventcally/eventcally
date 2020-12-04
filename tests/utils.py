import re
from flask import g, url_for
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup


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

    def create_form_data(self, response, values: dict) -> dict:
        from project.scrape.form import Form

        soup = BeautifulSoup(response.data, "html.parser")
        form = Form(soup.find("form"))
        return form.fill(values)

    def post_form(self, url, response, values: dict):
        data = self.create_form_data(response, values)
        return self._client.post(url, data=data)

    def post_json(self, url, data: dict):
        response = self._client.post(url, json=data)
        assert response.content_type == "application/json"
        return response.json

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

    def get_url(self, endpoint, **values):
        with self._app.test_request_context():
            url = url_for(endpoint, **values, _external=False)
        return url

    def get_ok(self, url):
        response = self._client.get(url)
        self.assert_response_ok(response)
        return response

    def assert_response_ok(self, response):
        assert response.status_code == 200

    def get_unauthorized(self, url):
        response = self._client.get(url)
        self.assert_response_unauthorized(response)
        return response

    def assert_response_unauthorized(self, response):
        assert response.status_code == 401

    def get_endpoint(self, endpoint, **values):
        return self._client.get(self.get_url(endpoint, **values))

    def get_endpoint_ok(self, endpoint, **values):
        return self.get_ok(self.get_url(endpoint, **values))

    def assert_response_redirect(self, response, endpoint, **values):
        assert response.status_code == 302

        redirect_url = "http://localhost" + self.get_url(endpoint, **values)
        assert response.headers["Location"] == redirect_url

    def assert_response_db_error(self, response):
        assert response.status_code == 200
        assert b"MockException" in response.data

    def assert_response_error_message(self, response, error_message=b"alert-danger"):
        assert response.status_code == 200
        assert error_message in response.data

    def assert_response_permission_missing(self, response, endpoint, **values):
        self.assert_response_redirect(response, endpoint, **values)
