export PYTHONPATH="${PYTHONPATH}:${PWD}"
pybabel extract -F babel.cfg  -k lazy_gettext -k dummy_gettext -k make_check_violation -k make_unique_violation -k get_text -k get_text_with_locale:2 -o messages.pot --sort-output .
pybabel init -i project/messages.pot -d project/translations -l de