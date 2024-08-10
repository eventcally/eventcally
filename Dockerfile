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
ENV DOCS_URL=""

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

RUN chmod u+x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
