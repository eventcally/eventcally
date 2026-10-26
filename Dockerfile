# Build the Vue frontend; Node is not part of the runtime image.
FROM node:22.23.4-slim AS frontend
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc frontend/
RUN cd frontend && npm ci
COPY frontend/ frontend/
COPY project/translations/ project/translations/
RUN cd frontend && npm run build

FROM python:3.12

# Add rsync
RUN apt update -qq && apt upgrade -y && apt autoremove -y
RUN apt install -y rsync redis-tools curl && apt autoremove -y

EXPOSE 5000

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Environment variables
ENV DATABASE_URL=""
ENV GOOGLE_MAPS_API_KEY=""
ENV MAIL_DEFAULT_SENDER=""
ENV MAIL_PASSWORD=""
ENV MAIL_PORT=""
ENV MAIL_SERVER=""
ENV MAIL_USERNAME=""
ENV SECRET_KEY=""
ENV SECURITY_PASSWORD_HASH=""
ENV SERVER_NAME=""
ENV STATIC_FILES_MIRROR=""
ENV REDIS_URL=""
ENV LIMITER_REDIS_URL=""
ENV DOCS_URL=""

# Docker image tag names (comma-separated), populated by the docker-build-push
# workflow build-arg and exposed at runtime (see the /up endpoint).
ARG APP_TAGS=""
ENV APP_TAGS=${APP_TAGS}

# uv, pinned; copied from its distroless image rather than installed via pip.
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /bin/

# Install into /opt/venv, outside /app: the pytest service in docker-compose.test.yml
# bind-mounts the repo over /app, which would hide an in-tree .venv. The dev group is
# included because that service, CI's build-image job and docker-compose.debug.yml
# (debugpy) run from this same image.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked

COPY . /app
COPY --from=frontend /src/project/presentation/web/static/dist /app/project/presentation/web/static/dist

RUN chmod u+x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
