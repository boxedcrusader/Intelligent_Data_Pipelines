import requests
import random
import time

BASE_URL = "http://127.0.0.1:8000"
DEVICE_ID = "sensor_01"
NUM_READINGS = 100


def send_reading(temperature: float, humidity: float) -> tuple[dict, float]:
    payload = {
        "device_id": DEVICE_ID,
        "temperature": temperature,
        "humidity": humidity,
    }

    start = time.perf_counter()
    response = requests.post(f"{BASE_URL}/sensors/data", json=payload)
    latency_ms = (time.perf_counter() - start) * 1000

    return response.json(), latency_ms


def run_simulation():
    print(f"Sending {NUM_READINGS} readings to {BASE_URL}...\n")

    latencies = []
    alerts_triggered = 0
    errors = 0

    for i in range(1, NUM_READINGS + 1):
        temperature = round(random.uniform(15.0, 35.0), 2)
        humidity = round(random.uniform(30.0, 80.0), 2)

        try:
            result, latency_ms = send_reading(temperature, humidity)
            latencies.append(latency_ms)

            # count alerts if your API returns them in the response
            if result.get("alerts"):
                alerts_triggered += len(result["alerts"])

            status = "ALERT" if result.get("alerts") else "OK"
            print(
                f"[{i:>3}] temp={temperature:.2f}°C  humid={humidity:.2f}%  "
                f"latency={latency_ms:.2f}ms  {status}"
            )

        except requests.RequestException as e:
            errors += 1
            print(f"[{i:>3}] Request failed: {e}")

    # ── Summary ──────────────────────────────────────────────
    if latencies:
        avg = sum(latencies) / len(latencies)
        minimum = min(latencies)
        maximum = max(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]

        print("\n" + "=" * 55)
        print("SIMULATION SUMMARY")
        print("=" * 55)
        print(f"  Total readings sent : {NUM_READINGS}")
        print(f"  Successful          : {len(latencies)}")
        print(f"  Errors              : {errors}")
        print(f"  Alerts triggered    : {alerts_triggered}")
        print(f"  Avg latency         : {avg:.2f} ms")
        print(f"  Min latency         : {minimum:.2f} ms")
        print(f"  Max latency         : {maximum:.2f} ms")
        print(f"  P95 latency         : {p95:.2f} ms")
        print("=" * 55)


if __name__ == "__main__":
    run_simulation()
    