# Development

## Dependencies

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock` (managed by [uv](https://docs.astral.sh/uv/)). Never edit `uv.lock` by hand.

```sh
uv sync                              # install runtime + dev dependencies into .venv
uv add <package>                     # add a runtime dependency
uv add --dev <package>               # add a dev dependency (pytest, linters, ...)
uv lock --upgrade-package <package>  # upgrade one package
```

## Docker

### Compose (including dependencies)

```sh
docker-compose up --build
```

### Build image

```sh
docker build -t eventcally/eventcally:latest .
```

### Run container with existing postgres server

```sh
docker run -p 5000:5000 -e "DATABASE_URL=postgresql://postgres@host.docker.internal/eventcally" eventcally/eventcally:latest
```

## Tests

### Run the full parallel suite (dockerized, no host Postgres/Redis needed)

```sh
./runtests.sh
```

### Run a single test or a subset

Pass the paths after `--`. The `--group` is what creates that group's database and
exports `TEST_DATABASE_URL`, so it is required even for one test — without it the run
fails with `could not translate host name "myserver"`. `--no-cov` skips collecting
coverage, which is only useful for the full suite.

```sh
./runtests.sh --splits 1 --group 1 -- tests/integration/presentation/web/views/test_event.py -v --no-cov
```

Tests under `tests/unit/` need no services and can also be run directly on the host
(`pytest tests/unit`) or in the container:

```sh
docker compose -f docker-compose.test.yml run --rm pytest pytest tests/unit -q
```

## Linting

Run all configured hooks:

```sh
pre-commit run --all-files
```

Run only architecture import checks (domain isolation contract):

```sh
lint-imports
```

## Database

### Create new revision

```sh
flask db migrate
```

### Upgrade database

```sh
flask db upgrade
```

## i18n

<https://python-babel.github.io/flask-babel/>

### Init

```sh
.scripts/translations/init.sh
```

### Add locale

```sh
.scripts/translations/add_locale.sh de
```

### Extract new msgid's and merge into \*.po files

```sh
.scripts/translations/extract.sh
```

#### Compile after translation is done

```sh
.scripts/translations/compile.sh
```

## Frontend (Vue 3)

The Vue 3 frontend lives in `frontend/` (Vite, TypeScript, bootstrap-vue-next). The Python side exposes it through the BFF channel (`project/presentation/bff`, JSON under `/bff`) and shell pages rendered with `layout_vue3.html` (Bootstrap 5 frame `layout_bs5.html`). The first area is the admin SPA at `/admin`.

```sh
npm ci --prefix frontend
npm run dev --prefix frontend                          # Vite dev server on :5173
VITE_DEV_SERVER_URL=http://localhost:5173 flask run    # Flask renders the shells and loads the dev server
npm run typecheck --prefix frontend
npm test --prefix frontend
npm run build --prefix frontend                        # writes project/presentation/web/static/dist/
```

The Docker image builds the bundle in a Node stage; Node is not needed at runtime.

With `docker-compose.debug.yml` the Vite dev server runs as the `vite` service (port 5173, hot reload) and `web` is started with `VITE_DEV_SERVER_URL`, so no local Node is needed:

```sh
docker compose -f docker-compose.yml -f docker-compose.debug.yml up
```

### API contract

BFF routes declare pydantic models with `bff_route`. The OpenAPI document and the TypeScript types are generated and committed; pytest and CI fail when they drift:

```sh
python -m project.presentation.bff.openapi > frontend/openapi.json
npm run gen:api --prefix frontend
```

### Frontend translations

The `.po` files stay the single source. Use literal `t("English msgid")` calls in `.vue`/`.ts` files; `.scripts/translations/extract.sh` picks them up and `npm run i18n --prefix frontend` converts the `.po` files to `frontend/src/locales/*.json` (also part of `npm run build`).

## Celery

```sh
dotenv run celery -A project.celery purge
```
