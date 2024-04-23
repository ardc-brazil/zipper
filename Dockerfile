FROM python:3.10.12-alpine as base

FROM base as builder

RUN mkdir /install
RUN apk update && apk add gcc python3-dev musl-dev
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
COPY . /app
RUN apk --no-cache add libpq
WORKDIR /app
EXPOSE 9092

CMD ["gunicorn", "-w 3", "-t 60" , "-b 0.0.0.0:9093", "app:create_app()", "--access-logfile -", "--error-logfile -"]
