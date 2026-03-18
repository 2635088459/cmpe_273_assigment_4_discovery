"""
User Service — a microservice that registers with the Service Registry.

Each instance:
1. Starts a Flask HTTP server on the given port
2. Serves user-lookup endpoints (/users, /users/<id>)
3. Registers itself with the Service Registry
4. Sends periodic heartbeats
5. Deregisters on graceful shutdown (Ctrl-C)

Usage:
    python example_service.py <service_name> <port>

Examples:
    python example_service.py user-service 8001
    python example_service.py user-service 8002
"""

import requests
import time
import signal
import sys
import os
import random
from threading import Thread, Event
from flask import Flask, jsonify, request as flask_request


# ---------------------------------------------------------------------------
# Registry helper (register / heartbeat / deregister)
# ---------------------------------------------------------------------------

REGISTRY_URL = os.environ.get("REGISTRY_URL", "http://localhost:5001")
HEARTBEAT_INTERVAL = 10  # seconds


def register_with_registry(service_name: str, address: str) -> bool:
    """POST /register to the Service Registry."""
    try:
        r = requests.post(
            f"{REGISTRY_URL}/register",
            json={"service": service_name, "address": address},
            timeout=5,
        )
        if r.status_code in (200, 201):
            print(f"✅ Registered {service_name} at {address}")
            return True
        else:
            print(f"❌ Registration failed ({r.status_code}): {r.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to registry at {REGISTRY_URL}")
        print("   Make sure the registry is running: python service_registry_improved.py")
        return False
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False


def deregister_from_registry(service_name: str, address: str):
    """POST /deregister to the Service Registry."""
    try:
        r = requests.post(
            f"{REGISTRY_URL}/deregister",
            json={"service": service_name, "address": address},
            timeout=5,
        )
        if r.status_code == 200:
            print(f"✅ Deregistered {service_name} at {address}")
        else:
            print(f"⚠️  Deregistration response: {r.text}")
    except Exception as e:
        print(f"⚠️  Deregistration error: {e}")


def heartbeat_loop(service_name: str, address: str, stop_event: Event):
    """Background thread — sends POST /heartbeat every HEARTBEAT_INTERVAL seconds."""
    while not stop_event.is_set():
        try:
            requests.post(
                f"{REGISTRY_URL}/heartbeat",
                json={"service": service_name, "address": address},
                timeout=5,
            )
            print(f"💓 Heartbeat sent for {service_name} ({address})")
        except Exception as e:
            print(f"⚠️  Heartbeat error: {e}")
        stop_event.wait(HEARTBEAT_INTERVAL)


# ---------------------------------------------------------------------------
# Flask micro-service (the actual HTTP endpoints that clients can call)
# ---------------------------------------------------------------------------

def create_service_app(service_name: str, port: int) -> Flask:
    """Return a Flask app that serves user data."""
    app = Flask(service_name)

    # --- simulated user database (same on every instance) ---
    USERS = {
        1:  {"id": 1,  "name": "Alice",   "email": "alice@example.com",   "role": "admin"},
        2:  {"id": 2,  "name": "Bob",     "email": "bob@example.com",     "role": "user"},
        3:  {"id": 3,  "name": "Charlie", "email": "charlie@example.com", "role": "user"},
        4:  {"id": 4,  "name": "Diana",   "email": "diana@example.com",   "role": "moderator"},
        5:  {"id": 5,  "name": "Eve",     "email": "eve@example.com",     "role": "user"},
    }

    @app.route("/users", methods=["GET"])
    def list_users():
        """Return all users."""
        return jsonify({
            "users": list(USERS.values()),
            "count": len(USERS),
            "served_by": f"{service_name}:{port}",
        })

    @app.route("/users/<int:user_id>", methods=["GET"])
    def get_user(user_id):
        """Look up a single user by ID."""
        user = USERS.get(user_id)
        if user is None:
            return jsonify({
                "error": "User not found",
                "user_id": user_id,
                "served_by": f"{service_name}:{port}",
            }), 404
        return jsonify({
            **user,
            "served_by": f"{service_name}:{port}",
        })

    @app.route("/info", methods=["GET"])
    def info():
        """Return basic information about this service instance."""
        return jsonify({
            "service": service_name,
            "port": port,
            "address": f"http://localhost:{port}",
            "status": "running",
            "pid": os.getpid(),
        })

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "service": service_name, "port": port})

    return app


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python example_service.py <service_name> <port>")
        print()
        print("Examples:")
        print("  python example_service.py user-service 8001")
        print("  python example_service.py user-service 8002")
        sys.exit(1)

    service_name = sys.argv[1]
    port = int(sys.argv[2])
    address = f"http://localhost:{port}"

    # 1) Register with the Service Registry
    if not register_with_registry(service_name, address):
        print("Exiting — could not register with registry.")
        sys.exit(1)

    # 2) Start heartbeat background thread
    stop_event = Event()
    hb_thread = Thread(target=heartbeat_loop, args=(service_name, address, stop_event), daemon=True)
    hb_thread.start()

    # 3) Graceful shutdown handler
    def shutdown(sig, frame):
        print("\n\n🛑 Shutting down gracefully...")
        stop_event.set()
        deregister_from_registry(service_name, address)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # 4) Start the Flask HTTP server
    print(f"\n {service_name} is running on http://localhost:{port}")
    print(f"   Endpoints: /users  /users/<id>  /info  /health")
    print("   Press Ctrl-C to stop\n")

    app = create_service_app(service_name, port)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
