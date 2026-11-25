from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.schemas.ticket import TicketInput, Classification


class TicketRepository:
    def __init__(self, db: Session): self.db = db

    def upsert_ticket(self, incoming: TicketInput, classification: Classification) -> Ticket:
        stmt = insert(Ticket).values(
            ticket_id=incoming.ticket_id, text=incoming.text,
            category=classification.category, confidence=classification.confidence,
            reason=classification.reason, status="pending", classified_at=datetime.now(timezone.utc)
        ).on_conflict_do_nothing(index_elements=["ticket_id"])
        self.db.execute(stmt)
        self.db.commit()
        ticket = self.db.scalar(select(Ticket).where(Ticket.ticket_id == incoming.ticket_id))
        return ticket


    def get_by_ticket_id(self, ticket_id: str) -> Ticket | None:
        return self.db.scalar(select(Ticket).where(Ticket.ticket_id == ticket_id))
