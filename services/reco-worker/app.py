import os
import random
import time
from fastapi import FastAPI, Response
import uvicorn

from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

PORT = int(os.getenv("PORT", "9091"))
endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

service_name = os.getenv("OTEL_SERVICE_NAME", "reco-worker")
resource = Resource.create({
    "service.name": service_name,
    "service.version": "1.0.0",
    "deployment.environment": "local"
})

tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces"))
)
trace.set_tracer_provider(tracer_provider)

metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics"),
    export_interval_millis=2000
)
metrics.set_meter_provider(
    MeterProvider(resource=resource, metric_readers=[metric_reader])
)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

CHAOS_ERROR_RATE = float(os.getenv("CHAOS_ERROR_RATE", "0.00"))
CHAOS_SLEEP_MS = int(os.getenv("CHAOS_SLEEP_MS", "0"))

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/reco")
def reco(user_id: str = "anon"):
    if CHAOS_SLEEP_MS > 0:
        time.sleep(CHAOS_SLEEP_MS / 1000.0)

    if random.random() < CHAOS_ERROR_RATE:
        return Response(content='{"error":"chaos injected"}', media_type="application/json", status_code=500)

    recs = [f"item_{(hash(user_id) + i) % 1000}" for i in range(10)]
    return {"recommendations": recs}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
