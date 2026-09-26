import random
from time import sleep

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.trace import Status, StatusCode


# ============================================================
# OpenTelemetry
# ============================================================

resource = Resource.create(
    {
        "service.name": "payment-api",
        "service.version": "1.0.0",
        "deployment.environment": "lab",
    }
)

provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

otlp_exporter = OTLPSpanExporter(
    endpoint="192.168.80.130:4317",
    insecure=True,
)

console_exporter = ConsoleSpanExporter()

provider.add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

provider.add_span_processor(
    BatchSpanProcessor(console_exporter)
)

tracer = trace.get_tracer("payment-api")


# ============================================================
# Helpers
# ============================================================

def get_trace_id():
    span = trace.get_current_span()
    span_context = span.get_span_context()

    return format(
        span_context.trace_id,
        "032x"
    )


# ============================================================
# Database
# ============================================================

def database_query():
    with tracer.start_as_current_span("database-query") as span:

        span.set_attribute(
            "db.system",
            "postgresql"
        )

        span.set_attribute(
            "db.operation.name",
            "SELECT"
        )

        print(
            f"Database query started "
            f"trace_id={get_trace_id()}",
            flush=True
        )

        sleep(0.3)

        print(
            f"Database query completed "
            f"trace_id={get_trace_id()}",
            flush=True
        )


# ============================================================
# External Payment Provider
# ============================================================

def external_api_call(should_fail):
    with tracer.start_as_current_span("external-api-call") as span:

        span.set_attribute(
            "http.request.method",
            "GET"
        )

        span.set_attribute(
            "server.address",
            "payment-provider.example.com"
        )

        print(
            f"Calling payment provider "
            f"trace_id={get_trace_id()}",
            flush=True
        )

        sleep(0.2)

        if should_fail:

            span.set_attribute(
                "http.response.status_code",
                500
            )

            print(
                f"Payment provider returned HTTP 500 "
                f"trace_id={get_trace_id()}",
                flush=True
            )

            error = RuntimeError(
                "Payment provider API returned HTTP 500"
            )

            span.record_exception(error)
            span.set_status(
                Status(
                    StatusCode.ERROR,
                    "Payment provider returned HTTP 500"
                )
            )

            raise error

        else:

            span.set_attribute(
                "http.response.status_code",
                200
            )

            print(
                f"Payment provider returned HTTP 200 "
                f"trace_id={get_trace_id()}",
                flush=True
            )


# ============================================================
# Payment Processing
# ============================================================

def process_payment(should_fail):

    with tracer.start_as_current_span(
        "process-payment"
    ) as span:

        span.set_attribute(
            "payment.method",
            "credit_card"
        )

        database_query()

        external_api_call(
            should_fail
        )


# ============================================================
# HTTP Request
# ============================================================

def handle_request():

    with tracer.start_as_current_span(
        "POST /api/payment"
    ) as span:

        span.set_attribute(
            "http.request.method",
            "POST"
        )

        span.set_attribute(
            "url.path",
            "/api/payment"
        )

        trace_id = get_trace_id()

        print(
            f"HTTP request started "
            f"trace_id={trace_id}",
            flush=True
        )

        # 5% failure rate
        should_fail = random.random() < 0.05

        try:

            process_payment(
                should_fail
            )

            span.set_attribute(
                "http.response.status_code",
                200
            )

            print(
                f"HTTP request completed "
                f"status=200 "
                f"trace_id={trace_id}",
                flush=True
            )

        except Exception as error:

            span.set_attribute(
                "http.response.status_code",
                500
            )

            span.record_exception(error)

            span.set_status(
                Status(
                    StatusCode.ERROR,
                    "Payment request failed"
                )
            )

            print(
                f"Application error: {error} "
                f"trace_id={trace_id}",
                flush=True
            )

            print(
                f"HTTP request completed "
                f"status=500 "
                f"trace_id={trace_id}",
                flush=True
            )


# ============================================================
# Main Loop
# ============================================================

def main():

    while True:

        handle_request()

        print(
            "Request finished. Waiting 5 seconds...",
            flush=True
        )

        sleep(5)


if __name__ == "__main__":
    main()
