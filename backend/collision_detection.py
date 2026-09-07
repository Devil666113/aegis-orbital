import numpy as np
from risk_model import evaluate_collision_risk
from conjunction_assessment import compute_tca, closest_distance


def compute_distance(pos1, pos2):

    p1 = np.array([pos1["x"], pos1["y"], pos1["z"]])
    p2 = np.array([pos2["x"], pos2["y"], pos2["z"]])

    return np.linalg.norm(p1 - p2)


def detect_collisions(positions, threshold=2):

    collisions = []

    n = len(positions)

    for i in range(n):
        for j in range(i + 1, n):

            sat1 = positions[i]
            sat2 = positions[j]

            # Compute time of closest approach
            tca = compute_tca(sat1, sat2)

            if tca is None:
                continue

            # Compute closest distance at that time
            closest_dist = closest_distance(sat1, sat2, tca)

            # Check if within collision threshold
            if closest_dist < threshold and closest_dist > 0.5:

                risk_data = evaluate_collision_risk(
                    sat1,
                    sat2,
                    closest_dist
                )

                risk_data["time_to_collision"] = round(float(tca), 2)

                collisions.append(risk_data)

    return collisions