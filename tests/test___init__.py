def test_mail_server():
    import os

    os.environ["DATABASE_URL"] = "postgresql://postgres@localhost/gsevpt_tests"
    os.environ["MAIL_SERVER"] = "mailserver.com"

    from project import app

    app.config["TESTING"] = True
    app.testing = True
