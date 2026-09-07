import numpy as np


def compute_relative_velocity(v1, v2):

    vel1 = np.array([v1["vx"], v1["vy"], v1["vz"]])
    vel2 = np.array([v2["vx"], v2["vy"], v2["vz"]])

    return np.linalg.norm(vel1 - vel2)


def compute_risk(distance, relative_velocity, object_size=1):

    if distance <= 0:
        return 1.0

    distance_factor = min(1.0, 1 / distance)
    velocity_factor = min(1.0, relative_velocity / 10)

    risk = (0.6 * distance_factor) + (0.3 * velocity_factor) + (0.1 * object_size)

    return round(float(risk), 3)


def evaluate_collision_risk(obj1, obj2, distance):

    relative_velocity = compute_relative_velocity(
        obj1["velocity"],
        obj2["velocity"]
    )

    risk_score = compute_risk(distance, relative_velocity)

    return {
        "satellite_1": obj1["name"],
        "satellite_2": obj2["name"],
        "distance_km": round(float(distance), 3),
        "relative_velocity": round(float(relative_velocity), 3),
        "risk_score": risk_score
    }