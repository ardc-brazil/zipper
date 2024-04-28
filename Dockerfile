FROM python:3.10.12-alpine as base

FROM base as builder

RUN mkdir /install
RUN apk update && apk add gcc python3-dev musl-dev libffi-dev
WORKDIR /install
COPY requirements.txt /requirements.txt
ARG ENV
COPY ${ENV}_config.yml /${ENV}_config.yml
RUN pip install --prefix=/install -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
COPY . /app
RUN apk --no-cache add libpq
WORKDIR /app
EXPOSE 9093

CMD ["uvicorn", "app:create_app", "--host", "0.0.0.0", "--port", "9093"]
