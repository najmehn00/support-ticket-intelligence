from pathlib import Path
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.ticket import Ticket
from app.schemas.ticket import TicketInput, TicketResult
from app.services.llm_service import LLMService, ModelError
from app.repositories.ticket_repository import TicketRepository

router = APIRouter(prefix="/tickets", tags=["tickets"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/classify", response_model=TicketResult)
async def classify_ticket(payload: TicketInput, db: Session = Depends(get_db)):
    repo = TicketRepository(db)
    existing = repo.get_by_ticket_id(payload.ticket_id)
    if existing:
        return TicketResult(ticket_id=existing.ticket_id, text=existing.text, category=existing.category,
                           confidence=existing.confidence, reason=existing.reason, status=existing.status)
    try:
        result = await LLMService().classify(payload.text)
    except ModelError as exc:
        raise HTTPException(status_code=502, detail="Classification service failed") from exc
    saved = repo.upsert_ticket(payload, result)
    return TicketResult(ticket_id=saved.ticket_id, text=saved.text, category=saved.category,
                       confidence=saved.confidence, reason=saved.reason, status=saved.status)


@router.post("/import")
async def import_dataset(db: Session = Depends(get_db)):
    path = Path("data/support_tickets_500.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Dataset file not found in data directory")
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Dataset is unreadable or invalid JSON") from exc
    repo = TicketRepository(db)
    service = LLMService()
    imported, skipped, errors = 0, 0, []
    for row in rows:
        try:
            payload = TicketInput.model_validate(row)
            if repo.get_by_ticket_id(payload.ticket_id):
                skipped += 1
                continue
            classification = await service.classify(payload.text)
            repo.upsert_ticket(payload, classification)
            imported += 1
        except ModelError:
            errors.append({"ticket_id": row.get("ticket_id"), "error": "classification_failed"})
        except Exception:
            errors.append({"ticket_id": row.get("ticket_id"), "error": "processing_failed"})
    return {"imported": imported, "skipped_duplicates": skipped, "failed": len(errors), "errors": errors[:20]}


@router.get("/{ticket_id}", response_model=TicketResult)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = TicketRepository(db).get_by_ticket_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketResult(ticket_id=ticket.ticket_id, text=ticket.text, category=ticket.category,
                       confidence=ticket.confidence, reason=ticket.reason, status=ticket.status)
