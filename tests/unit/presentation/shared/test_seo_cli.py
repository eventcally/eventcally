from flask import Flask

from project.presentation.cli import seo as seo_cli_module


def test_commands_call_the_seo_service(monkeypatch):
    calls = []
    monkeypatch.setattr(
        seo_cli_module.seo, "generate_sitemap", lambda: calls.append("sitemap")
    )
    monkeypatch.setattr(
        seo_cli_module.seo, "generate_robots_txt", lambda: calls.append("robots")
    )
    app = Flask(__name__)
    app.cli.add_command(seo_cli_module.seo_cli)
    runner = app.test_cli_runner()

    assert runner.invoke(args=["seo", "generate-sitemap"]).exit_code == 0
    assert runner.invoke(args=["seo", "generate-robots-txt"]).exit_code == 0
    assert calls == ["sitemap", "robots"]
