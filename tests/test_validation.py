import pytest
from pydantic import ValidationError
from app.schemas.ticket import TicketInput, Classification

def test_ticket_input_rejects_blank_text():
    with pytest.raises(ValidationError):
        TicketInput(ticket_id="T-1", text="  ")

def test_category_is_restricted():
    with pytest.raises(ValidationError):
        Classification(category="sales", confidence=0.9, reason="bad category")
