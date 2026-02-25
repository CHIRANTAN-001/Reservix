# Distributed Event Booking System

A high-concurrency event booking system designed to safely reserve and confirm seats using Redis-based lease locking and PostgreSQL optimistic concurrency control.

This project simulates a real-world ticket booking architecture where multiple users can reserve seats concurrently without overselling inventory.

The system uses Redis for temporary seat reservations and PostgreSQL as the permanent source of truth for confirmed bookings.

---

## Core Features

* Event and section-based seat allocation
* Redis-based lease locking for temporary seat reservations
* Optimistic concurrency control for permanent inventory updates
* Automatic seat restoration after reservation expiry
* Booking lifecycle state management
* Inventory consistency guarantees
* High concurrency-safe seat allocation

---

## Architecture Overview

The system separates **temporary reservations** from **permanent inventory**.

### Temporary Layer (Redis)

Redis is used for fast seat reservations during checkout.

Each section has an availability key:

```
section:{event_id}:{section_id} -> available_seats
```

When a user reserves seats:

```
DECRBY section:{event_id}:{section_id} N
```

A booking lock key is created:

```
booking:{booking_id}
TTL = 10 minutes
```

This acts as a lease-based lock that temporarily reserves seats.

If the booking expires, seats are restored automatically.

---

### Permanent Layer (PostgreSQL)

PostgreSQL stores confirmed inventory and booking records.

#### Bookings Table

```
bookings
- id
- user_id
- event_id
- section_id
- seats_requested
- status (HOLD | CONFIRMED | EXPIRED | FAILED)
- expires_at
```

#### Section Inventory Table

```
section_inventory
- section_id (PK)
- total_capacity
- available_seats
- version
```

Inventory is updated only when a booking is confirmed.

```
available_seats = available_seats - N
version = version + 1
```

---

## Booking Lifecycle

### 1. Hold Seats

```
POST /bookings/hold
```

Steps:

1. Redis availability decreased atomically
2. Booking created with status HOLD
3. Redis lock key created with TTL

Seats remain reserved for 10 minutes.

---

### 2. Confirm Booking

```
POST /bookings/{id}/confirm
```

Steps:

1. Booking status updated atomically:

```
HOLD → CONFIRMED
```

2. Section inventory updated using optimistic concurrency control

3. Redis lock removed

Seats become permanently sold.

---

### 3. Expired Booking

If the user does not complete payment:

1. Booking becomes EXPIRED
2. Seats restored in Redis
3. Inventory unchanged

---

## Concurrency Strategy

This system uses **two-layer concurrency protection**.

### Layer 1 — Redis Lease Locking

Redis prevents overselling during the checkout process.

Atomic operations:

```
DECRBY section:{event}:{section} N
```

This ensures multiple users cannot reserve the same seats simultaneously.

---

### Layer 2 — Optimistic Concurrency Control

PostgreSQL prevents permanent data inconsistencies.

Inventory updates use a version column:

```
version = version + 1
```

This protects against:

* Payment race conditions
* Duplicate confirmations
* Redis restarts
* Retry storms

---

## Recovery Mechanisms

### Expiry Worker

Background job restores seats for expired bookings:

```
status HOLD → EXPIRED
INCRBY section key
```

---

### Redis Rebuild

If Redis restarts, inventory can be rebuilt from PostgreSQL:

```
section_inventory.available_seats
→ Redis section keys
```

---

## Tech Stack

* FastAPI
* PostgreSQL
* Redis
* SQLAlchemy Async
* Python
* Pydantic

---

## Design Goals

* Prevent seat overselling
* Handle high concurrency
* Support distributed systems
* Self-healing inventory
* Strong data consistency

---

## Future Improvements

* Redis Cluster support
* Payment gateway integration
* Kafka-based event processing
* Seat-level reservations
* Admin analytics dashboard
* Load testing and benchmarking

---

## Key Concepts Demonstrated

* Lease-based distributed locking
* Optimistic concurrency control
* Eventual consistency
* Inventory reservation systems
* High-concurrency backend design
