import random


def evasive_maneuver(event):
    """
    Simulate a simple orbital adjustment to avoid collision.
    """

    adjustment = random.uniform(0.2, 1.0)

    print(f"Orbit adjusted by +{round(adjustment,3)} km")

    return {
        "maneuver": True,
        "adjustment_km": round(adjustment, 3),
        "satellite": event["satellite_1"]
    }