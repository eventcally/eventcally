import io

from project.infrastructure.babel_extract import babel_extract_frontend


def extract(source: str):
    return list(babel_extract_frontend(io.BytesIO(source.encode()), [], [], {}))


def test_extracts_literal_keys_with_line_numbers():
    result = extract("<template>\n  {{ t('Users') }} <b>{{ t(\"Email\") }}</b>\n")

    assert result == [
        (2, "gettext", "Users", []),
        (2, "gettext", "Email", []),
    ]


def test_ignores_dynamic_keys_and_lookalikes():
    assert extract('t(key)\nformat("x")\nconst t = 1') == []


def test_unescapes_quotes():
    assert extract("t('It\\'s')")[0][2] == "It's"


def test_extracts_calls_wrapped_onto_their_own_line():
    result = extract('const d = t(\n  "If set, wrapped.",\n);')

    assert result == [(2, "gettext", "If set, wrapped.", [])]
