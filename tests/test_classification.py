import pytest
from unittest.mock import patch
from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_mock_classifies_refund_as_billing():
    with patch("app.services.llm_service.settings.llm_mode", "mock"):
        result = await LLMService().classify("پیگیری بازپرداخت پول")

    assert result.category == "billing"
    assert 0 <= result.confidence <= 1