from flask import Flask

from project.presentation.web.requests import _content_security_policy


def test_csp_default():
    app = Flask(__name__)
    csp = _content_security_policy(app)
    assert "localhost:5173" not in csp
    assert "connect-src 'self' blob: data:;" in csp


def test_csp_allows_vite_dev_server():
    app = Flask(__name__)
    app.config["VITE_DEV_SERVER_URL"] = "http://localhost:5173/"
    csp = _content_security_policy(app)
    assert (
        "script-src 'self' 'unsafe-eval' 'unsafe-inline' http://localhost:5173;" in csp
    )
    assert "ws://localhost:5173" in csp
