import re
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup
from flask import g, url_for
from sqlalchemy.exc import IntegrityError


class UtilActions(object):
    def __init__(self, client, app):
        self._client = client
        self._app = app
        self._access_token = None
        self._refresh_token = None
        self._client_id = None
        self._client_secret = None

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
                    "accept_tos": "y",
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
        from tests.form import Form

        soup = BeautifulSoup(response.data, "html.parser")
        form = Form(soup.find("form"))
        return form.fill(values)

    def post_form_data(self, url, data: dict):
        return self._client.post(url, data=data)

    def post_form(self, url, response, values: dict):
        data = self.create_form_data(response, values)
        return self.post_form_data(url, data=data)

    def get_headers(self):
        headers = dict()

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        return headers

    def log_request(self, url):
        print(url)

    def log_json_request(self, url, data: dict):
        self.log_request(url)
        print(data)

    def log_response(self, response):
        print(response.status_code)
        print(response.data)
        print(response.json)

    def post_json(self, url, data: dict):
        self.log_json_request(url, data)
        response = self._client.post(url, json=data, headers=self.get_headers())
        self.log_response(response)
        return response

    def put_json(self, url, data: dict):
        self.log_json_request(url, data)
        response = self._client.put(url, json=data, headers=self.get_headers())
        self.log_response(response)
        return response

    def patch_json(self, url, data: dict):
        self.log_json_request(url, data)
        response = self._client.patch(url, json=data, headers=self.get_headers())
        self.log_response(response)
        return response

    def delete(self, url):
        self.log_request(url)
        response = self._client.delete(url, headers=self.get_headers())
        self.log_response(response)
        return response

    def mock_db_commit(self, mocker, orig=None):
        mocked_commit = mocker.patch("project.db.session.commit")
        mocked_commit.side_effect = IntegrityError(
            "MockException", "MockException", orig
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

    def get(self, url):
        return self._client.get(url)

    def get_ok(self, url):
        response = self.get(url)
        self.assert_response_ok(response)
        return response

    def assert_response_ok(self, response):
        assert response.status_code == 200

    def assert_response_created(self, response):
        assert response.status_code == 201

    def assert_response_no_content(self, response):
        assert response.status_code == 204

    def assert_response_unprocessable_entity(self, response):
        assert response.status_code == 422

    def assert_response_bad_request(self, response):
        assert response.status_code == 400

    def assert_response_api_error(self, response, message):
        assert response.json["name"] == message

    def get_unauthorized(self, url):
        response = self._client.get(url)
        self.assert_response_unauthorized(response)
        return response

    def assert_response_unauthorized(self, response):
        assert response.status_code == 401

    def assert_response_notFound(self, response):
        assert response.status_code == 404

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

    def parse_query_parameters(self, url):
        query = urlsplit(url).query
        params = parse_qs(query)
        return {k: v[0] for k, v in params.items()}

    def authorize(self, client_id, client_secret, scope):
        # Authorize-Seite öffnen
        redirect_uri = self.get_url("swagger_oauth2_redirect")
        url = self.get_url(
            "authorize",
            response_type="code",
            client_id=client_id,
            scope=scope,
            redirect_uri=redirect_uri,
        )
        response = self.get_ok(url)

        # Authorisieren
        response = self.post_form(
            url,
            response,
            {},
        )

        assert response.status_code == 302
        assert redirect_uri in response.headers["Location"]

        # Code aus der Redirect-Antwort lesen
        params = self.parse_query_parameters(response.headers["Location"])
        assert "code" in params
        code = params["code"]

        # Mit dem Code den Access-Token abfragen
        token_url = self.get_url("issue_token")
        response = self.post_form_data(
            token_url,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "authorization_code",
                "scope": scope,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )

        self.assert_response_ok(response)
        assert response.content_type == "application/json"
        assert "access_token" in response.json
        assert "expires_in" in response.json
        assert "refresh_token" in response.json
        assert response.json["scope"] == scope
        assert response.json["token_type"] == "Bearer"

        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = response.json["access_token"]
        self._refresh_token = response.json["refresh_token"]

    def refresh_token(self):
        token_url = self.get_url("issue_token")
        response = self.post_form_data(
            token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )

        self.assert_response_ok(response)
        assert response.content_type == "application/json"
        assert response.json["token_type"] == "Bearer"
        assert "access_token" in response.json
        assert "expires_in" in response.json

        self._access_token = response.json["access_token"]

    def revoke_token(self):
        url = self.get_url("revoke_token")
        response = self.post_form_data(
            url,
            data={
                "token": self._access_token,
                "token_type_hint": "access_token",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )

        self.assert_response_ok(response)
