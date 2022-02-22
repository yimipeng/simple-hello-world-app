FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install -r requirement.txt

RUN opentelemetry-bootstrap --action=install

EXPOSE 8000

ENV HOME=/

ENV OTEL_RESOURCE_ATTRIBUTES='service.name=web-application-autoInstr-test'

CMD OTEL_PROPAGATORS=xray OTEL_PYTHON_ID_GENERATOR=xray opentelemetry-instrument python3 hello.py
