import os
import logging
from azure.monitor.opentelemetry import configure_azure_monitor

logger = logging.getLogger("brand-guardian-telemetry")


def setup_telemetry():
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

    if not connection_string:
        logger.warning("No Application Insights connection string found. Telemetry disabled.")
        return

    try:
        configure_azure_monitor(
            connection_string=connection_string,
            logger_name="brand-guardian-tracer"
        )
        logger.info("Azure Monitor telemetry enabled.")
    except Exception as e:
        logger.error(f"Failed to initialize Azure Monitor: {e}")