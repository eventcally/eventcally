from project.presentation.shared.rate_limit import rate_limit_rows


class _Provider:
    def get_rate_limit_key(self):
        return "apikey-rate-limit-rows"

    def get_rate_limit_value(self):
        return "5/minute;10/day"


def test_rate_limit_rows_list_every_limit_with_its_remaining_requests(app):
    with app.test_request_context():
        rows = rate_limit_rows(_Provider())

    assert rows == ["5 per 1 minute: 5 remaining", "10 per 1 day: 10 remaining"]
