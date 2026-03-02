# Reservix – Distributed Event Booking System

A high-performance, distributed event booking system designed to handle high-concurrency seat reservations with guaranteed inventory consistency. Reservix safely manages concurrent bookings using Redis-based lease locking and PostgreSQL optimistic concurrency control—proven patterns for production ticketing systems.

<div align="center">

**[Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [API](#api) • [Contributing](#contributing)**

</div>

---

## Features

✅ **Distributed Seat Reservations** — Redis-backed temporary holds with automatic expiry  
✅ **Guaranteed Inventory Safety** — Optimistic concurrency control prevents overselling  
✅ **High Concurrency** — Designed to handle thousands of concurrent booking requests  
✅ **Self-Healing** — Automatic seat restoration for expired bookings via background workers  
✅ **Event Lifecycle Management** — Full user authentication, event creation, and booking workflows  
✅ **FastAPI REST API** — Modern async/await API with automatic documentation  
✅ **Docker Ready** — Multi-stage builds with PostgreSQL and Redis services  

---

## Why Reservix?

If you're building a ticketing or reservation system, you'll face these challenges:

- **Overselling Risk**: Multiple users booking the same seat simultaneously
- **Race Conditions**: Payment processing while inventory updates happen
- **Distributed Systems**: Handling Redis restarts and network failures gracefully
- **High Load**: Supporting thousands of concurrent users

Reservix solves these with a two-layer approach:
1. **Redis Layer** — Fast temporary holds with automatic expiry (10 minutes)
2. **PostgreSQL Layer** — Permanent inventory with versioning to prevent race conditions

See [Architecture](#architecture) for technical details.

---

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 12+
- Redis 6.0+
- Docker & Docker Compose (optional)

### Option 1: Docker Compose (Recommended)

```bash
git clone https://github.com/yourusername/Reservix.git
cd Reservix

# Start all services (API, workers, PostgreSQL, Redis)
docker-compose up
```

The API will be available at `http://localhost:8000`

### Option 2: Local Development

Clone and install dependencies:

```bash
git clone https://github.com/yourusername/Reservix.git
cd Reservix

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Configure environment:

```bash
# Create .env from template
cp .env.example .env

# Update with your PostgreSQL and Redis credentials
# DATABASE_URL=postgresql://user:password@localhost:5432/Reservix
# REDIS_URL=redis://localhost:6379
```

Run migrations:

```bash
alembic upgrade head
```

Start the API server:

```bash
python -m app.main
```

Start background workers (in separate terminals):

```bash
# Expiry worker (handles expired bookings)
python -m app.workers.expiry_worker

# Capacity reconciliation worker (syncs Redis ↔ PostgreSQL)
python -m app.workers.capacity_reconciliation_worker
```

View API documentation at: `http://localhost:8000/docs`

---

## API Usage

### 1. Create a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

### 2. Get Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

### 3. Create an Event

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Concert 2026",
    "event_date": "2026-06-15",
    "sections": [
      {
        "name": "VIP",
        "capacity": 100
      }
    ]
  }'
```

### 4. Hold Seats (Temporary Reservation)

```bash
curl -X POST http://localhost:8000/api/v1/bookings/hold \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "event-123",
    "section_id": "VIP",
    "seats_requested": 2
  }'
```

**Response:**
```json
{
  "booking_id": "booking-456",
  "status": "HOLD",
  "expires_at": "2026-03-02T14:10:00Z"
}
```

Seats are temporarily reserved for **10 minutes**. If not confirmed within this window, they're automatically released.

### 5. Confirm Booking (Permanent)

```bash
curl -X POST http://localhost:8000/api/v1/bookings/booking-456/confirm \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Once confirmed, seats are permanently sold and captured in the PostgreSQL inventory.

---

## Architecture

Reservix uses a **two-layer concurrency strategy** to handle high-volume bookings safely.

```
User Request
    ↓
    ├─→ [Redis Layer] Fast temporary holds (10 min TTL)
    │   └─→ Atomic DECRBY reduces available seats
    ├─→ [Payment Processing] External payment gateway
    └─→ [PostgreSQL Layer] Permanent confirmation
        └─→ Optimistic locking (version column) prevents race conditions
```

### Temporary Layer (Redis)

When a user holds seats:

1. Redis key `section:{event_id}:{section_id}` is decremented atomically
2. A booking lock key is created with 10-minute TTL
3. Booking record saved to PostgreSQL with status `HOLD`

**If TTL expires:** Expiry worker automatically increments Redis key back, freeing the seats.

### Permanent Layer (PostgreSQL)

When a booking is confirmed:

1. Booking status changes from `HOLD` → `CONFIRMED`  
2. Section inventory updated with optimistic concurrency control (version check)
3. Redis lock removed

Each `section_inventory` row has:
- `available_seats` — Current inventory count
- `version` — Incremented on every update (detects race conditions)

This prevents duplicate confirmations and payment race conditions.

### Background Workers

**Expiry Worker:**
- Scans for bookings with status `HOLD` past their expiry time
- Updates status to `EXPIRED` and restores seats in Redis

**Capacity Reconciliation Worker:**
- Periodically syncs Redis inventory with PostgreSQL
- Rebuilds Redis from PostgreSQL if it crashes/restarts

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for deep technical details.

---

## Project Structure

```
Reservix/
├── app/
│   ├── main.py                 # FastAPI app factory & lifespan
│   ├── core/
│   │   ├── config.py           # Environment settings
│   │   ├── database.py         # SQLAlchemy async session
│   │   ├── redis.py            # Redis client
│   │   └── response.py         # Exception handlers
│   ├── models/                 # SQLAlchemy orm models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── repositories/           # Data access layer
│   ├── services/               # Business logic
│   ├── workers/                # Background jobs
│   └── api/v1/
│       └── endpoints/          # Route handlers
├── migrations/                 # Alembic database migrations
├── docker-compose.yml          # Local dev environment
├── requirements.txt            # Python dependencies
└── README.md
```

---

## Configuration

All configuration is environment-based via `.env` file:

```env
# App
APP_NAME=Reservix
APP_VERSION=1.0.0
APP_DEBUG=True
ENVIRONMENT=development
PORT=8000

# Database (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Reservix
DB_USER=postgres
DB_PASSWORD=password

# Cache (Redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_USER=default
REDIS_PASSWORD=password

# Security
SECRET_KEY=your-secret-key-here
HASHING_ALG=HS256
ACCESS_TOKEN_EXPIRE_SECONDS=3600

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

---

## Database Migrations

Reservix uses [Alembic](https://alembic.sqlalchemy.org/) for schema management.

Create a new migration:
```bash
alembic revision --autogenerate -m "Add new column"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

---

## Getting Help

- **API Documentation**: Start the server and visit `http://localhost:8000/docs`

---
### Development Workflow

```bash
# Set up dev environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI 0.129+ |
| **Async ORM** | SQLAlchemy 2.0+ |
| **Database** | PostgreSQL 12+ |
| **Cache** | Redis 6.0+ |
| **Validation** | Pydantic V2 |
| **Migrations** | Alembic 1.18+ |
| **Logging** | Loguru |
| **Security** | PyJWT, bcrypt |
| **Python** | 3.12+ |

---

## Key Design Patterns

- **Lease-Based Locking** — Redis TTL acts as a distributed lock
- **Optimistic Concurrency Control** — Version column detects conflicts
- **Repository Pattern** — Clean data access abstraction
- **Service Layer** — Business logic separation
- **Worker Pattern** — Async background job processing
- **Async/Await** — Non-blocking I/O throughout

---

## Roadmap

- [ ] Redis Cluster support for HA
- [ ] Kafka integration for distributed events
- [ ] Seat-level reservations (not just section counts)
- [ ] Admin analytics dashboard
- [ ] Payment gateway integration
- [ ] Load testing suite & benchmarks

---

**Built with ❤️ for high-concurrency systems**
