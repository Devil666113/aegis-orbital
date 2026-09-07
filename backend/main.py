from tle_fetcher import fetch_tle_data
from tle_parser import parse_tle_data
from orbit_engine import compute_satellite_position
from collision_detection import detect_collisions
from event_logger import log_collision
from maneuver_engine import evasive_maneuver

from datetime import datetime, UTC, timedelta
import time
import random


def print_collision_warning(collision):

    print("\n⚠ COLLISION WARNING")
    print("-----------------------------")

    print("Time        :", datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"))

    print("Satellite   :", collision["satellite_1"])
    print("Object      :", collision["satellite_2"])

    print("Closest Dist:", collision["distance_km"], "km")
    print("Rel Velocity:", collision["relative_velocity"], "km/s")

    print("Risk Score  :", collision["risk_score"])
    print("Impact ETA  :", collision["time_to_collision"], "seconds")

    if collision["risk_score"] > 0.7:
        level = "HIGH"
    elif collision["risk_score"] > 0.4:
        level = "MEDIUM"
    else:
        level = "LOW"

    print("Risk Level  :", level)
    print("-----------------------------\n")


def main():

    print("\nAegis Orbital Monitoring Started\n")

    # Load satellite data
    raw_data = fetch_tle_data()
    satellites = parse_tle_data(raw_data)

    # Limit for CPU safety
    satellites = satellites[:200]

    print("Satellites loaded:", len(satellites))

    # Simulation time (important for tracking)
    simulation_time = datetime.now(UTC)

    start_time = time.time()

    while True:

        # Advance simulation time
        simulation_time += timedelta(seconds=5)

        positions = []

        # Generate satellite positions (time-based tracking)
        for sat in satellites:

            result = compute_satellite_position(sat, simulation_time)

            if result:
                positions.append(result)

        # Add simulated debris
        for _ in range(5):

            target = random.choice(positions)

            debris = {
                "name": f"DEBRIS-{random.randint(1000,9999)}",
                "position": {
                    "x": target["position"]["x"] + random.uniform(-1, 1),
                    "y": target["position"]["y"] + random.uniform(-1, 1),
                    "z": target["position"]["z"] + random.uniform(-1, 1)
                },
                "velocity": {
                    "vx": random.uniform(-8, 8),
                    "vy": random.uniform(-8, 8),
                    "vz": random.uniform(-8, 8)
                }
            }

            positions.append(debris)

        # Detect collisions
        collisions = detect_collisions(positions)

        print("Tracked Objects :", len(positions))
        print("Potential Risks :", len(collisions))

        if collisions:

            # Sort by highest risk
            collisions.sort(key=lambda x: x["risk_score"], reverse=True)

            top_events = collisions[:3]

            for event in top_events:

                print_collision_warning(event)

                log_collision(event)

                # Autonomous maneuver
                if event["risk_score"] > 0.7:

                    print("AUTONOMOUS EVASIVE MANEUVER EXECUTED")

                    evasive_maneuver(event)

        # System metrics
        uptime = int(time.time() - start_time)

        print("Active Satellites :", len(satellites))
        print("Debris Objects    :", len(positions) - len(satellites))
        print("Total Objects     :", len(positions))
        print("System Uptime     :", uptime, "seconds")
        print("-----\n")

        # Loop delay
        time.sleep(5)


if __name__ == "__main__":
    main()