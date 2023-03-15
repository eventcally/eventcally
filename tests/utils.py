import pathlib
import re
from urllib.parse import parse_qs, urlsplit

import googlemaps
from bs4 import BeautifulSoup
from flask import g, url_for
from sqlalchemy.exc import IntegrityError


class UtilActions(object):
    def __init__(self, client, app, mocker, requests_mock):
        self._client = client
        self._app = app
        self._mocker = mocker
        self._requests_mock = requests_mock
        self._access_token = None
        self._refresh_token = None
        self._client_id = None
        self._client_secret = None
        self._ajax_csrf = None

        self.gmaps_places_autocomplete_query = self._mocker.patch.object(
            googlemaps.Client, "places_autocomplete_query", return_value=list()
        )
        self.gmaps_place = self._mocker.patch.object(
            googlemaps.Client, "place", return_value=dict()
        )

    def get_access_token(self):
        return self._access_token

    def get_refresh_token(self):
        return self._refresh_token

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
            self.assert_response_success_message(response)

    def login(
        self,
        email="test@test.de",
        password="MeinPasswortIstDasBeste",
        follow_redirects=True,
    ):
        from project.services.user import find_user_by_email

        with self._app.app_context():
            user = find_user_by_email(email)
            assert user

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
                follow_redirects=follow_redirects,
            )

            if follow_redirects:
                assert response.status_code == 200
            else:
                assert response.status_code == 302

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

    def get_ajax_csrf(self, response):
        pattern = 'var csrf_token = "(.*)";'
        match = re.search(pattern.encode("utf-8"), response.data)

        if not match:
            return None

        return match.group(1).decode("utf-8")

    def get_soup(self, response) -> BeautifulSoup:
        return BeautifulSoup(response.data, "html.parser")

    def create_form_data(self, response, values: dict) -> dict:
        from tests.form import Form

        soup = self.get_soup(response)
        form = Form(soup.find("form"))
        return form.fill(values)

    def post_form_data(self, url, data: dict):
        return self._client.post(url, data=data, headers=self.get_headers())

    def post_form(self, url, response, values: dict):
        data = self.create_form_data(response, values)
        return self.post_form_data(url, data=data)

    def get_headers(self):
        headers = dict()

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        if self._ajax_csrf:
            headers["X-CSRFToken"] = self._ajax_csrf

        return headers

    def log_request(self, url):
        print(url)

    def log_json_request(self, url, data: dict = None):
        self.log_request(url)

        if data:
            print(data)

    def log_response(self, response):
        print(response.status_code)
        print(response.data)
        print(response.json)

    def get_json(self, url):
        self.log_request(url)
        response = self._client.get(url, headers=self.get_headers())
        self.log_response(response)
        return response

    def post_json(self, url, data: dict):
        self.log_json_request(url, data)
        response = self._client.post(url, json=data, headers=self.get_headers())
        self.log_response(response)
        return response

    def put_json(self, url, data: dict = None):
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
        return mocker.patch("project.views.utils.send_mails_with_body")

    def assert_send_mail_called(
        self, mock, expected_recipients, expected_contents=None
    ):
        mock.assert_called_once()
        args, kwargs = mock.call_args
        send_recipients, subject, body, html = args

        if not isinstance(expected_recipients, list):
            expected_recipients = [expected_recipients]

        assert len(send_recipients) == len(expected_recipients)

        for expected_recipient in expected_recipients[:]:
            assert (
                expected_recipient in send_recipients
            ), f"{expected_recipient} not in recipients"

        if expected_contents:
            if not isinstance(expected_contents, list):
                expected_contents = [expected_contents]

            for content in expected_contents:
                assert content in body, f"{content} not in body"
                assert content in html, f"{content} not in html"

    def mock_now(self, mocker, year, month, day):
        from project.dateutils import create_berlin_date

        now = create_berlin_date(year, month, day)
        mocker.patch("project.dateutils.get_now", return_value=now)

    def get_url(self, endpoint, **values):
        with self._app.test_request_context():
            url = url_for(endpoint, **values, _external=False)
        return url

    def get_image_url(self, image, **values):
        from project.jinja_filters import url_for_image

        with self._app.test_request_context():
            url = url_for_image(image, **values, _external=False)
        return url

    def get_image_url_for_id(self, image_id, **values):
        from project.models import Image

        with self._app.app_context():
            image = Image.query.get(image_id)
            url = self.get_image_url(image, **values)
        return url

    def get(self, url):
        response = self._client.get(url)

        if response.status_code == 200:
            self._ajax_csrf = self.get_ajax_csrf(response)

        return response

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
        return response

    def assert_response_forbidden(self, response):
        assert response.status_code == 403

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

    def assert_response_contains_alert(self, response, category, message=None):
        assert response.status_code == 200

        soup = self.get_soup(response)
        alerts = soup.find_all("div", class_="alert-" + category)
        assert len(alerts) > 0

        if not message:
            return

        for alert in alerts:
            if message in alert.text:
                return

        assert False, "Alert not found"

    def assert_response_error_message(self, response, message=None):
        self.assert_response_contains_alert(response, "danger", message)

    def assert_response_db_error(self, response):
        self.assert_response_error_message(response, "MockException")

    def assert_response_success_message(self, response, message=None):
        self.assert_response_contains_alert(response, "success", message)

    def assert_response_permission_missing(self, response, endpoint, **values):
        self.assert_response_redirect(response, endpoint, **values)

    def assert_response_contains(self, response, needle):
        assert needle.encode("UTF-8") in response.data

    def assert_response_contains_not(self, response, needle):
        assert needle.encode("UTF-8") not in response.data

    def parse_query_parameters(self, url):
        query = urlsplit(url).query
        params = parse_qs(query)
        return {k: v[0] for k, v in params.items()}

    def authorize(self, client_id, client_secret, scope):
        # Authorize-Seite öffnen
        redirect_uri = self.get_url("swagger_oauth2_redirect")
        url = self.get_url(
            "authorize",
            nonce=4711,
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

    def introspect(self, token, token_type_hint):
        url = self.get_url("introspect")
        response = self.post_form_data(
            url,
            data={
                "token": token,
                "token_type_hint": token_type_hint,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )

        self.assert_response_ok(response)

    def get_oauth_userinfo(self):
        url = self.get_url("oauth_userinfo")
        return self.get_json(url)

    def mock_get_request_with_text(self, url: str, text: str):
        self._requests_mock.get(url, text=text)

    def mock_get_request_with_content(self, url: str, content):
        self._requests_mock.get(url, content=content)

    def mock_get_request_with_file(self, url: str, path: pathlib.Path, filename: str):
        text = (path / filename).read_text()
        self.mock_get_request_with_text(url, text)

    def mock_image_request_with_file(self, url: str, path: pathlib.Path, filename: str):
        content = (path / filename).read_bytes()
        self.mock_get_request_with_content(url, content)
