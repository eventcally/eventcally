export PYTHONPATH="${PYTHONPATH}:${PWD}"
pybabel extract -F babel.cfg -k lazy_gettext -k dummy_gettext -o messages.pot --sort-output .
pybabel update -N -i messages.pot -d project/translations