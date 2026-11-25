from sqlalchemy import text, select, func

from app.models.ticket import Ticket, RoutingLog


def create_ticket(db_session, ticket_id, category):
    ticket = Ticket(
        ticket_id=ticket_id,
        text="Test support ticket",
        category=category,
        confidence=0.95,
        reason="Test reason",
        status="pending",
    )
    db_session.add(ticket)
    db_session.flush()
    return ticket


def call_route_ticket(db_session, ticket_id, destination):
    result = db_session.execute(
        text("""
            SELECT route_ticket(
                CAST(:ticket_id AS UUID),
                :destination
            )
        """),
        {
            "ticket_id": str(ticket_id),
            "destination": destination,
        },
    )
    return result.scalar_one()


def test_route_ticket_with_correct_destination(db_session):
    ticket = create_ticket(db_session, "ROUTE-001", "billing")

    result = call_route_ticket(db_session, ticket.id, "finance")

    db_session.refresh(ticket)

    assert result is True
    assert ticket.status == "routed"
    assert ticket.routed_at is not None

    log_count = db_session.scalar(
        select(func.count()).select_from(RoutingLog).where(
            RoutingLog.ticket_id == ticket.id
        )
    )
    assert log_count == 1


def test_route_ticket_rejects_wrong_destination(db_session):
    ticket = create_ticket(db_session, "ROUTE-002", "billing")

    result = call_route_ticket(db_session, ticket.id, "technical")

    db_session.refresh(ticket)

    assert result is False
    assert ticket.status == "pending"
    assert ticket.routed_at is None

    log_count = db_session.scalar(
        select(func.count()).select_from(RoutingLog).where(
            RoutingLog.ticket_id == ticket.id
        )
    )
    assert log_count == 0


def test_route_ticket_prevents_duplicate_routing(db_session):
    ticket = create_ticket(db_session, "ROUTE-003", "technical")

    first_result = call_route_ticket(
        db_session, ticket.id, "technical"
    )
    second_result = call_route_ticket(
        db_session, ticket.id, "technical"
    )

    db_session.refresh(ticket)

    assert first_result is True
    assert second_result is False
    assert ticket.status == "routed"

    log_count = db_session.scalar(
        select(func.count()).select_from(RoutingLog).where(
            RoutingLog.ticket_id == ticket.id
        )
    )
    assert log_count == 1