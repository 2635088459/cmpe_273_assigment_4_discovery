"""
Service Discovery Client - Discovers service instances and calls a random one.

This script:
1. Queries the Service Registry for all instances of a given service
2. Randomly selects one instance
3. Calls the selected instance's /users/<id> endpoint
4. Prints the response — including which instance served the request

Usage:
    python discover_and_call.py                     # defaults to "user-service"
    python discover_and_call.py <service_name>      # discover specific service
    python discover_and_call.py <service_name> <N>  # call N times to show randomness

Examples:
    python discover_and_call.py user-service
    python discover_and_call.py user-service 5
"""

import requests
import random
import sys
import os

REGISTRY_URL = os.environ.get("REGISTRY_URL", "http://localhost:5001")
USER_IDS = [1, 2, 3, 4, 5]  # IDs available in the simulated DB


def discover_instances(service_name: str) -> list:
    """Ask the registry for all active instances of *service_name*."""
    url = f"{REGISTRY_URL}/discover/{service_name}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get("instances", [])
        else:
            print(f"❌ Discovery failed ({r.status_code}): {r.text}")
            return []
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to registry at {REGISTRY_URL}")
        print("   Make sure the registry is running: python service_registry_improved.py")
        return []
    except Exception as e:
        print(f"❌ Discovery error: {e}")
        return []


def call_instance(address: str, endpoint: str) -> dict | None:
    """Send a GET request to *address*/*endpoint* and return the JSON body."""
    url = f"{address}{endpoint}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()
    except Exception as e:
        print(f"❌ Call to {url} failed: {e}")
        return None


def main():
    service_name = sys.argv[1] if len(sys.argv) > 1 else "user-service"
    num_calls = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print("=" * 60)
    print("SERVICE DISCOVERY CLIENT")
    print("=" * 60)
    print(f"Registry : {REGISTRY_URL}")
    print(f"Service  : {service_name}")
    print(f"Calls    : {num_calls}")
    print()

    # ---- Step 1: Discover ----
    print(f"🔍 Discovering instances of '{service_name}' ...")
    instances = discover_instances(service_name)

    if not instances:
        print(f"\n❌ No active instances found for '{service_name}'.")
        print("   Did you start the service instances?")
        print(f"   Example:  python example_service.py {service_name} 8001")
        sys.exit(1)

    print(f"   Found {len(instances)} instance(s):")
    for inst in instances:
        print(f"   • {inst['address']}  (uptime {inst['uptime_seconds']:.1f}s)")
    print()

    # ---- Step 2: Call random instance(s) ----
    for i in range(1, num_calls + 1):
        chosen = random.choice(instances)
        addr = chosen["address"]
        user_id = random.choice(USER_IDS)
        endpoint = f"/users/{user_id}"
        print(f"📞 Call {i}/{num_calls} → {addr}{endpoint}")
        result = call_instance(addr, endpoint)
        if result:
            served = result.get("served_by", "?")
            name   = result.get("name", result.get("error", "?"))
            print(f"   ✅ User: {name}  |  served_by: {served}")
        else:
            print(f"   ❌ No response from {addr}")
        print()

    print("Done! ")


if __name__ == "__main__":
    main()
