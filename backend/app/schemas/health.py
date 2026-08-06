from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "unhealthy"]
    service: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "ok",
                    "service": "Urban Exploration Platform API",
                    "version": "0.1.0",
                    "environment": "development",
                    "timestamp": "2026-06-29T12:00:00Z",
                }
            ]
        }
    }
