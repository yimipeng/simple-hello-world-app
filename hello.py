import boto3
from flask import Flask
from __future__ import print_function
import os
import time
import json 
import requests
import decimal

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.sdk.extension.aws.trace import AwsXRayIdGenerator

from opentelemetry import propagate
from opentelemetry.sdk.extension.aws.trace.propagation.aws_xray_format import AwsXRayFormat

from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor

from opentelemetry.sdk.extension.aws.trace.propagation.aws_xray_format import (
    TRACE_ID_DELIMITER,
    TRACE_ID_FIRST_PART_LENGTH,
    TRACE_ID_VERSION,
)

from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

    
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.set_tracer_provider(TracerProvider(active_span_processor=span_processor, id_generator=AwsXRayIdGenerator()))

propagate.set_global_textmap(AwsXRayFormat())

app = Flask(__name__)

BotocoreInstrumentor().instrument()
# Initialize `Instrumentor` for the `requests` library
RequestsInstrumentor().instrument()
# Initialize `Instrumentor` for the `flask` web framework
FlaskInstrumentor().instrument_app(app)


dynamodb = boto3.resource("dynamodb", region_name='us-east-1')

table = dynamodb.Table('ProductCatalog')


def convert_otel_trace_id_to_xray(otel_trace_id_decimal):
    otel_trace_id_hex = "{:032x}".format(otel_trace_id_decimal)
    x_ray_trace_id = TRACE_ID_DELIMITER.join(
        [
            TRACE_ID_VERSION,
            otel_trace_id_hex[:TRACE_ID_FIRST_PART_LENGTH],
            otel_trace_id_hex[TRACE_ID_FIRST_PART_LENGTH:],
        ]
    )
    return '{{"traceId": "{}"}}'.format(x_ray_trace_id)


@app.route('/')
def hello_world():
    try:
        response = table.get_item(
            Key={
                'pk': "0"
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("GetItem succeeded:")
        print(json.dumps(response['Item'], indent=4, cls=DecimalEncoder))
    return 'Thanks for using AWS App Runner!'
@app.route('/health')
def health_check():
    return 'health check'

# Test HTTP instrumentation
@app.route("/outgoing-http-call")
def call_http():
    requests.get("https://aws.amazon.com/")

    return app.make_response(
        convert_otel_trace_id_to_xray(
            trace.get_current_span().get_span_context().trace_id
        )
    )


if __name__ == '__main__':
    app.run(threaded=True, host="0.0.0.0", debug=True, port=int(os.environ.get("PORT", 8000)))
    

    
