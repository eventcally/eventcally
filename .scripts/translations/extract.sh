export PYTHONPATH="${PYTHONPATH}:${PWD}"
# No .env is loaded on purpose: extraction builds no Flask app and touches no
# database, so it needs no environment. (It also cannot safely source .env --
# unquoted values containing spaces, such as JWT_PRIVATE_KEY, break both
# `xargs` and `.`-sourcing.)
pybabel extract -F babel.cfg -k lazy_gettext -k dummy_gettext -k make_check_violation -k make_unique_violation -k get_text -k get_text_with_locale:2 -o messages.pot --sort-output .
pybabel update -N -i messages.pot -d project/translations