FROM python:3.7-slim-buster

EXPOSE 5000

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

RUN chmod u+x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
