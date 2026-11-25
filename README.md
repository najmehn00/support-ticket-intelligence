# Support Ticket Intelligence & Routing System

A ticket classification and automated routing system built with **FastAPI, PostgreSQL, an LLM provider, and n8n**.

The application imports support tickets, classifies them into three categories, stores the results in PostgreSQL, and routes pending tickets to the appropriate destination through an n8n workflow.

## 1. Features

- Import and validate support tickets from a JSON dataset.
- Classify tickets using an LLM, with both mock and real API modes.
- Store tickets, classifications, and routing logs in PostgreSQL.
- Automatically route tickets through n8n every five minutes.
- Prevent duplicate ticket imports and duplicate routing logs.
- Handle invalid input, model failures, and timeouts.
- Provide REST API documentation through Swagger UI.

## 2. Ticket Categories

| Category | Description | Routing destination |
|---|---|---|
| `billing` | Payments, invoices, charges, and refunds | `finance` |
| `technical` | Login, application, API, upload, and technical problems | `technical` |
| `manual_review` | Ambiguous, unsupported, or unclassifiable requests | `manual_review` |

## 3. Requirements

- Docker Desktop
- Docker Compose
- Python 3.11 or later (for running tests locally)

## 4. Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Configure the environment variables:

```env
DATABASE_URL=postgresql+psycopg://tickets:tickets@db:5432/tickets

LLM_MODE=mock
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=20
CONFIDENCE_THRESHOLD=0.65
```

### Mock mode

Set `LLM_MODE=mock` to run the application without an external API key or API costs. This mode is intended for local development and testing.

### Real LLM mode

Set `LLM_MODE=real` and provide a valid API key and provider configuration:

```env
LLM_MODE=real
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

Use a compatible API provider if you change the base URL or model.

**Never commit `.env` or expose API credentials.**

## 5. Run the application

Build and start the services:

```bash
docker compose up --build
```

The services are available at:

| Service | URL |
|---|---|
| FastAPI | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| n8n | http://localhost:5678 |

## 6. Import tickets

The dataset is located at:

```text
data/support_tickets_500.json
```

Import the tickets using:

```bash
curl -X POST http://localhost:8000/tickets/import
```

The import endpoint validates and processes the dataset. Existing ticket IDs are skipped, so repeated imports do not create duplicate records or reset already processed tickets.

## 7. API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check application health |
| POST | `/tickets/classify` | Classify and persist a single ticket |
| POST | `/tickets/import` | Import and process the dataset |
| GET | `/tickets/{ticket_id}` | Retrieve a ticket by its ID |


## 8. Database initialization

PostgreSQL automatically executes the SQL initialization scripts in `database/` when the database is created with a fresh data volume.

The `route_ticket` function is installed automatically during the first database initialization.

For an existing database volume where the function has not been installed, run:

```bash
docker compose exec -T db psql -U tickets -d tickets < database/route_ticket.sql
```

## 9. n8n automated routing

The n8n workflow is provided in the `n8n/workflows/` directory.

To configure it:

1. Open n8n at http://localhost:5678.
2. Import the provided workflow JSON.
3. Configure the PostgreSQL credentials for the database service:
   - Host: `db`
   - Port: `5432`
   - Database: `tickets`
   - User and password: use the values configured in `.env`.
4. Ensure the PostgreSQL routing function in `database/route_ticket.sql` has been installed.
5. Save and publish the workflow.

The workflow runs every five minutes and:

1. Fetches pending tickets that do not already have routing logs.
2. Uses a Switch node to identify the ticket category.
3. Routes billing tickets to `finance`.
4. Routes technical tickets to `technical`.
5. Routes ambiguous tickets to `manual_review`.
6. Records each successful routing operation in `routing_logs`.

The workflow processes up to 100 tickets per execution.

Routing is performed through a PostgreSQL function that validates the destination, records the routing log, and updates the ticket status in a single database transaction. This prevents duplicate routing and ensures that a ticket is marked as routed only after its routing log is successfully inserted.

## 10. Database design

The application uses PostgreSQL with two main tables:

- `tickets`: stores ticket text, category, confidence, classification reason, status, and timestamps.
- `routing_logs`: stores the destination and timestamp of each successful routing operation.

Each ticket can have at most one routing log.

## 11. Run tests

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the test suite:

```bash
docker compose exec api python -m pytest -v
```


The test suite contains 14 tests covering:
- Mock classification.
- Ticket import and duplicate handling.
- LLM failure handling.
- Input validation.
- Ticket creation and retrieval.
- Correct routing destinations.
- Rejection of invalid routing destinations.
- Prevention of duplicate routing.

## 12. Project structure

```text
support-ticket-intelligence/
├── app/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── data/
│   └── support_tickets_500.json
├── database/
│   └── route_ticket.sql
├── n8n/
│   └── workflows/
├── tests/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── README.md
```
