# Load .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

export PYTHONPATH="${PYTHONPATH}:${PWD}"
pybabel extract -F babel.cfg -k lazy_gettext -k dummy_gettext -k make_check_violation -k make_unique_violation -o messages.pot --sort-output .
pybabel update -N -i messages.pot -d project/translations