from app.core.config import settings
from app.schemas.fund import ModelHealthResponse
from app.services.repository import mock_last_train_at


def get_model_health() -> ModelHealthResponse:
    return ModelHealthResponse(
        short_model_version=settings.model_short_version,
        mid_model_version=settings.model_mid_version,
        last_train_at=mock_last_train_at(),
        coverage_rate=0.97,
    )
