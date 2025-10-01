"""
Optional OpenTelemetry initialization (safe no-op if deps or config absent).
"""

import os
import logging

logger = logging.getLogger(__name__)


def init_observability(service_name: str = "customercaregpt-backend") -> None:
    """Initialize tracing/metrics only when explicitly enabled.

    This function is safe to call even if OpenTelemetry deps are not installed
    or env vars are missing. It will fail open (no-ops).
    """
    try:
        enabled = os.getenv("OTEL_ENABLED", "false").lower() == "true"
        if not enabled:
            return

        # Lazy imports to avoid hard dependency
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor  # type: ignore
            sqlalchemy_available = True
        except Exception:
            sqlalchemy_available = False

        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

        resource = Resource.create({
            "service.name": service_name,
        })
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces"))
        provider.add_span_processor(processor)

        # Defer FastAPI instrumentation to caller (needs app instance)
        # Instrument requests/httpx
        RequestsInstrumentor().instrument()

        logger.info("OpenTelemetry tracing initialized", extra={"endpoint": otlp_endpoint})

        # Return a helper for app instrumentation
        def instrument_fastapi(app):
            try:
                FastAPIInstrumentor.instrument_app(app)
            except Exception:
                pass
            return app

        # Attach helper on module for caller usage
        globals()["instrument_fastapi_app"] = instrument_fastapi

        # Optionally instrument SQLAlchemy if available
        if sqlalchemy_available:
            try:
                SQLAlchemyInstrumentor().instrument()
            except Exception:
                pass

    except Exception as e:
        logger.warning("OpenTelemetry init skipped", extra={"error": str(e)})


