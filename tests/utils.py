import pathlib
import re
from urllib.parse import parse_qs, urlsplit

import googlemaps
from bs4 import BeautifulSoup
from flask import g, url_for
from flask_security.utils import url_for_security
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
        self._api_key = None

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
    ):
        from project.services.user import find_user_by_email

        response = self._client.get("/login")
        assert response.status_code == 200

        with self._app.app_context():
            with self._client:
                response = self._client.post(
                    "/login",
                    data={
                        "email": email,
                        "password": password,
                        "csrf_token": self.get_csrf(response),
                        "submit": "Anmelden",
                    },
                )

                assert response.status_code == 302
                assert g.identity.user.email == email

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
        pattern = r"xhr\.setRequestHeader\(\"X-CSRFToken\", \"(.*)\"\);"
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

    def post_form_data(self, url, data: dict, **kwargs):
        headers = self.get_headers()

        if "headers" in kwargs:
            headers.update(kwargs["headers"])

        return self._client.post(url, data=data, headers=headers)

    def post_form(self, url, response, values: dict):
        data = self.create_form_data(response, values)
        return self.post_form_data(url, data=data)

    def get_headers(self):
        headers = dict()

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        if self._ajax_csrf:
            headers["X-CSRFToken"] = self._ajax_csrf

        if self._api_key:
            headers["X-API-Key"] = self._api_key

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

        if response.status_code == 200 and response.data:
            danger_alerts = self.get_response_danger_alerts(response)
            if danger_alerts:
                print("Danger alerts:")
                print(danger_alerts)

    def get_json(self, url, **kwargs):
        self.log_request(url)
        headers = self.get_headers()

        if "headers" in kwargs:
            headers.update(kwargs["headers"])

        response = self._client.get(url, headers=headers)
        self.log_response(response)
        return response

    def get_json_ok(self, url, **kwargs):
        response = self.get_json(url, **kwargs)
        self.assert_response_ok(response)
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

    def mock_send_mails_async(self, mocker):
        return mocker.patch("project.views.utils.send_mails_with_signatures_async")

    def assert_send_mail_called(
        self, mock, expected_recipients, expected_contents=None
    ):
        mock.assert_called_once()
        args, kwargs = mock.call_args

        if mock._extract_mock_name() == "send_mails_with_signatures_async":
            signatures = args[0]
            send_recipients = [s[0] for s in signatures]
            first_signature = signatures[0]
            _, subject, body, html = first_signature
        else:
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
        from project import db
        from project.models import Image

        with self._app.app_context():
            image = db.session.get(Image, image_id)
            url = self.get_image_url(image, **values)
        return url

    def get(self, url, **kwargs):
        response = self._client.get(url, **kwargs)

        if response.status_code == 200:
            self._ajax_csrf = self.get_ajax_csrf(response)

        return response

    def get_ok(self, url, **kwargs):
        response = self.get(url, **kwargs)
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
        redirect_url = self.get_url(endpoint, **values)
        self.assert_response_redirect_to_url(response, redirect_url)

    def assert_response_redirect_to_url(self, response, redirect_url):
        self.assert_status_code(response, 302)

        absolute_url = "http://localhost" + redirect_url
        response_location = response.headers["Location"]

        assert (
            response_location == redirect_url or response_location == absolute_url
        ), f"{response_location} != {redirect_url} != {absolute_url}"

    def assert_status_code(self, response, status_code):
        if response.status_code != status_code:
            self.log_response(response)

        assert response.status_code == status_code

    def assert_response_redirect_to_login(self, response, next_url):
        assert response.status_code == 302

        with self._client:
            with self._app.test_request_context():
                redirect_url = url_for_security("login", next=next_url)

        self.assert_response_redirect_to_url(response, redirect_url)

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

    def get_response_alerts(self, response, category):
        soup = self.get_soup(response)
        alerts = soup.find_all("div", class_="alert-" + category)
        return " ".join([a.text for a in alerts])

    def get_response_danger_alerts(self, response):
        return self.get_response_alerts(response, "danger")

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
        self._get_token(
            client_id, client_secret, scope, "authorization_code", code, redirect_uri
        )

    def setup_api_key(self, api_key):
        self._api_key = api_key

    def grant_client_credentials(self, client_id, client_secret, scope):
        # Mit den Credentials den Access-Token abfragen
        self._get_token(client_id, client_secret, scope, "client_credentials")

    def _get_token(
        self, client_id, client_secret, scope, grant_type, code=None, redirect_uri=None
    ):
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": grant_type,
            "scope": scope,
        }

        if grant_type == "authorization_code":
            data["code"] = code
            data["redirect_uri"] = redirect_uri

        token_url = self.get_url("issue_token")
        response = self.post_form_data(token_url, data=data)

        self.assert_response_ok(response)
        assert response.content_type == "application/json"
        assert "access_token" in response.json
        assert "expires_in" in response.json

        if grant_type == "authorization_code":
            assert "refresh_token" in response.json

        from project.api import replace_legacy_scopes

        assert response.json["scope"] == replace_legacy_scopes(scope)
        assert response.json["token_type"] == "Bearer"

        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = response.json["access_token"]

        if grant_type == "authorization_code":
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

    def ajax_lookup(self, url: str, field_name: str, term: str = ""):
        ajax_url = f"{url}?field_name={field_name}&term={term}"
        ajax_response = self.get_json_ok(
            ajax_url, headers={"X-Backend-For-Frontend": "ajax_lookup"}
        )
        return ajax_response

    def ajax_validation(self, url: str, field_name: str, field_value: str, expected):
        ajax_url = f"{url}?field_name={field_name}"
        ajax_response = self.post_form_data(
            ajax_url,
            {
                field_name: field_value,
            },
            headers={"X-Backend-For-Frontend": "ajax_validation"},
        )

        if expected is True:
            assert ajax_response.json is True
        else:
            assert isinstance(ajax_response.json, str)

    def ajax_google_places(self, url: str, field_name: str, keyword: str):
        ajax_url = f"{url}?field_name={field_name}"
        ajax_response = self.post_form_data(
            ajax_url,
            {
                "keyword": keyword,
            },
            headers={"X-Backend-For-Frontend": "google_places"},
        )
        self.assert_response_ok(ajax_response)
        return ajax_response

    def ajax_google_place(self, url: str, field_name: str, gmaps_id: str):
        ajax_url = f"{url}?field_name={field_name}"
        ajax_response = self.post_form_data(
            ajax_url,
            {
                "gmaps_id": gmaps_id,
            },
            headers={"X-Backend-For-Frontend": "google_place"},
        )
        self.assert_response_ok(ajax_response)
        return ajax_response
