from datetime import datetime, UTC


def log_collision(event):

    with open("collision_log.txt", "a") as f:

        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

        line = (
            f"{timestamp} | "
            f"{event['satellite_1']} vs {event['satellite_2']} | "
            f"distance={event['distance_km']} km | "
            f"risk={event['risk_score']}\n"
        )

        f.write(line)