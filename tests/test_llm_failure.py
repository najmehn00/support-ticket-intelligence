import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.services.llm_service import LLMService, ModelError


def test_real_mode_without_key_fails_cleanly(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "real")
    monkeypatch.setattr(settings, "llm_api_key", None)

    with pytest.raises(ModelError):
        asyncio.run(LLMService().classify("test ticket"))


def test_classification_returns_502_on_llm_failure(client):
    with patch(
        "app.api.routes.tickets.LLMService.classify",
        new_callable=AsyncMock,
        side_effect=ModelError("LLM unavailable"),
    ):
        response = client.post(
            "/tickets/classify",
            json={
                "ticket_id": "LLM-FAIL-TEST-001",
                "text": "مشکل در پرداخت سفارش",
            },
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "Classification service failed"
