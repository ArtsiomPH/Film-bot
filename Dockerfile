FROM python:3.10-alpine

ENV PATH="$PATH:/etc/secrets/.env"

COPY requirements.txt /requirements.txt

RUN apk update && apk upgrade && apk add bash

RUN pip install -r /requirements.txt

COPY . .

CMD ["python3", "film_bot.py"]