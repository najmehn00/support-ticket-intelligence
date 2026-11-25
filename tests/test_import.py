import json
from unittest.mock import AsyncMock, patch

from app.schemas.ticket import Classification


def test_import_dataset_success(client):
    rows = [
        {"ticket_id": "IMPORT-001", "text": "مشکل در پرداخت سفارش"},
        {"ticket_id": "IMPORT-002", "text": "خطا هنگام ورود به برنامه"},
    ]

    classification = Classification(
        category="billing",
        confidence=0.95,
        reason="Test classification",
    )

    with (
        patch("app.api.routes.tickets.Path.exists", return_value=True),
        patch(
            "app.api.routes.tickets.Path.read_text",
            return_value=json.dumps(rows, ensure_ascii=False),
        ),
        patch(
            "app.api.routes.tickets.LLMService.classify",
            new_callable=AsyncMock,
            return_value=classification,
        ) as mock_classify,
    ):
        response = client.post("/tickets/import")

    assert response.status_code == 200
    assert response.json()["imported"] == 2
    assert response.json()["skipped_duplicates"] == 0
    assert response.json()["failed"] == 0
    assert mock_classify.await_count == 2


def test_import_dataset_skips_duplicates(client):
    rows = [
        {"ticket_id": "IMPORT-DUP-001", "text": "مشکل پرداخت سفارش"},
    ]

    classification = Classification(
        category="billing",
        confidence=0.95,
        reason="Test classification",
    )

    with (
        patch("app.api.routes.tickets.Path.exists", return_value=True),
        patch(
            "app.api.routes.tickets.Path.read_text",
            return_value=json.dumps(rows, ensure_ascii=False),
        ),
        patch(
            "app.api.routes.tickets.LLMService.classify",
            new_callable=AsyncMock,
            return_value=classification,
        ) as mock_classify,
    ):
        first = client.post("/tickets/import")
        second = client.post("/tickets/import")

    assert first.json()["imported"] == 1
    assert second.json()["imported"] == 0
    assert second.json()["skipped_duplicates"] == 1
    assert second.json()["failed"] == 0
    mock_classify.assert_awaited_once()


def test_import_dataset_file_not_found(client):
    with patch("app.api.routes.tickets.Path.exists", return_value=False):
        response = client.post("/tickets/import")

    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset file not found in data directory"