import boto3
from flask import Flask
import os
import time
import json 
import requests

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.sdk.extension.aws.trace import AwsXRayIdGenerator

from opentelemetry import propagate
# from opentelemetry.sdk.extension.aws.trace.propagation.aws_xray_format import AwsXRayFormat
from opentelemetry.propagators.aws import AwsXRayPropagator

from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor


otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.set_tracer_provider(TracerProvider(active_span_processor=span_processor, id_generator=AwsXRayIdGenerator()))

# propagate.set_global_textmap(AwsXRayFormat())
propagate.set_global_textmap(AwsXRayPropagator())

app = Flask(__name__)

BotocoreInstrumentor().instrument()
# Initialize `Instrumentor` for the `requests` library
RequestsInstrumentor().instrument()
# Initialize `Instrumentor` for the `flask` web framework
FlaskInstrumentor().instrument_app(app)

@app.route('/')
def hello_world():
    return 'Hello World! App Runner'
@app.route('/health')
def health_check():
    return 'health check'

if __name__ == '__main__':
    app.run(threaded=True, host="0.0.0.0", debug=True, port=int(os.environ.get("PORT", 8000)))
    

    
