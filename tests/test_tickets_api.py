from unittest.mock import AsyncMock, patch

from app.schemas.ticket import Classification


def test_classify_and_get_ticket(client):
    classification = Classification(
        category="billing",
        confidence=0.95,
        reason="Payment issue",
    )

    with patch(
        "app.api.routes.tickets.LLMService.classify",
        new_callable=AsyncMock,
        return_value=classification,
    ) as mock_classify:
        response = client.post(
            "/tickets/classify",
            json={
                "ticket_id": "API-TEST-001",
                "text": "مبلغ از حسابم کسر شده است",
            },
        )

    assert response.status_code == 200
    assert response.json()["category"] == "billing"
    assert response.json()["status"] == "pending"
    mock_classify.assert_awaited_once()

    get_response = client.get("/tickets/API-TEST-001")

    assert get_response.status_code == 200
    assert get_response.json()["ticket_id"] == "API-TEST-001"
    assert get_response.json()["category"] == "billing"


def test_duplicate_ticket_does_not_call_llm_again(client):
    classification = Classification(
        category="technical",
        confidence=0.9,
        reason="Login issue",
    )

    with patch(
        "app.api.routes.tickets.LLMService.classify",
        new_callable=AsyncMock,
        return_value=classification,
    ) as mock_classify:
        first_response = client.post(
            "/tickets/classify",
            json={
                "ticket_id": "API-DUPLICATE-001",
                "text": "هنگام ورود خطا دریافت می‌کنم",
            },
        )

        second_response = client.post(
            "/tickets/classify",
            json={
                "ticket_id": "API-DUPLICATE-001",
                "text": "متن متفاوت برای همان تیکت",
            },
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["text"] == "هنگام ورود خطا دریافت می‌کنم"
    assert second_response.json()["category"] == "technical"
    mock_classify.assert_awaited_once()


def test_get_nonexistent_ticket_returns_404(client):
    response = client.get("/tickets/DOES-NOT-EXIST")

    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket not found"
