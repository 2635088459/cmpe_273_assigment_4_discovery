# Architecture — Microservice with Service Discovery

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                          System Overview                             │
│                                                                      │
│   ┌────────────────────────────────────────────────────────────┐    │
│   │           Service Registry  (port 5001)                    │    │
│   │                                                            │    │
│   │   In-Memory Store                                          │    │
│   │   ┌──────────────────────────────────────────────────┐    │    │
│   │   │ "user-service": [                                │    │    │
│   │   │    { addr: ":8001", heartbeat: "..." },          │    │    │
│   │   │    { addr: ":8002", heartbeat: "..." }           │    │    │
│   │   │ ]                                                │    │    │
│   │   └──────────────────────────────────────────────────┘    │    │
│   │                                                            │    │
│   │   Background Cleanup Thread                                │    │
│   │   • removes instances with no heartbeat > 30 s             │    │
│   └────────────────────────────────────────────────────────────┘    │
│                          ▲          ▲                                │
│            register +    │          │   discover                     │
│            heartbeat     │          │                                │
│         ┌────────────────┘          └──────────────┐                │
│         │                                          │                │
│   ┌─────┴──────────┐                     ┌────────┴─────────┐      │
│   │ user-service   │                     │  Discovery Client │      │
│   │ Instance 1     │◀── call /users/<id> ─│  discover_and_   │      │
│   │ :8001          │    (random pick)    │  call.py          │      │
│   ├────────────────┤                     └────────┬─────────┘      │
│   │ user-service   │◀── call /users/<id> ─────────┘                │
│   │ Instance 2     │    (random pick)                               │
│   │ :8002          │                                                │
│   └────────────────┘                                                │
└──────────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### 1. Service Registry (`service_registry_improved.py`)

The central coordination point.  All microservice instances register here and
clients query here to find available instances.

- **Technology**: Python / Flask
- **Port**: 5001
- **Storage**: In-memory Python dictionary protected by `threading.Lock`
- **Cleanup**: A daemon thread runs every 10 s and removes instances whose last
  heartbeat is older than 30 s.

**Endpoints**

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/register` | Register `{service, address}` |
| POST | `/heartbeat` | Update heartbeat timestamp |
| POST | `/deregister` | Remove an instance |
| GET | `/discover/<service>` | Return active instances |
| GET | `/services` | List all services + counts |
| GET | `/health` | Registry health check |

### 2. Microservice Instance (`example_service.py`)

A **User Service** that both **registers itself** with the registry and
**serves user-lookup endpoints** that other services / clients can call.

- **Technology**: Python / Flask
- **Port**: user-specified (e.g. 8001, 8002)
- **On start**: `POST /register` → registry
- **Background**: heartbeat thread every 10 s
- **On Ctrl-C**: `POST /deregister` → registry (graceful shutdown)

**Endpoints**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/users` | List all users |
| GET | `/users/<id>` | Look up user by ID (response includes `served_by`) |
| GET | `/info` | Return service name, port, PID |
| GET | `/health` | Instance health check |

### 3. Discovery Client (`discover_and_call.py`)

A short-lived client script that demonstrates the full discovery → call flow.

1. `GET /discover/<service>` → registry returns list of active instances.
2. `random.choice(instances)` → pick one address.
3. `GET <address>/users/<id>` → call the chosen instance.
4. Print the response (includes `served_by` to show which instance handled it).  Repeat N times.

---

## Request Flow Diagrams

### Registration & Heartbeat

```
example_service.py                        service_registry_improved.py
      │                                              │
      │  POST /register                              │
      │  { service: "user-service",                  │
      │    address: "http://localhost:8001" }         │
      ├─────────────────────────────────────────────▶│
      │                                              │ store in registry dict
      │  201 { status: "registered" }                │
      │◀─────────────────────────────────────────────┤
      │                                              │
      │         ┌── every 10 s ──┐                   │
      │         │ POST /heartbeat│                   │
      │         └────────────────┘                   │
      ├─────────────────────────────────────────────▶│
      │  200 { status: "ok" }                        │
      │◀─────────────────────────────────────────────┤
```

### Discovery & Random Call

```
discover_and_call.py            registry              example_service (8001 or 8002)
      │                            │                            │
      │ GET /discover/user-service │                            │
      ├───────────────────────────▶│                            │
      │                            │ filter active instances    │
      │ 200 { instances: [...] }   │                            │
      │◀───────────────────────────┤                            │
      │                            │                            │
      │ random.choice(instances)   │                            │
      │ ─── pick one ──────────────┼── GET /users/3 ───────────▶│
      │                            │                            │ look up user
      │                            │  200 { name: "Charlie",   │
      │                            │    served_by: ":8001" }    │
      │◀───────────────────────────┼────────────────────────────┤
      │ print response             │                            │
```

### Graceful Shutdown

```
example_service.py                        service_registry_improved.py
      │  Ctrl-C (SIGINT)                             │
      │                                              │
      │  POST /deregister                            │
      │  { service, address }                        │
      ├─────────────────────────────────────────────▶│
      │                                              │ remove from registry
      │  200 { status: "deregistered" }              │
      │◀─────────────────────────────────────────────┤
      │  exit                                        │
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| In-memory storage | Simple for a demo; no external DB dependency |
| Thread-safe registry | `threading.Lock` prevents race conditions |
| Heartbeat + auto-cleanup | Detects crashed instances without manual intervention |
| Client-side random selection | Demonstrates load balancing at the client level |
| Flask for both registry and services | Consistent stack; minimal dependencies |
