import numpy as np


def vector(v):
    return np.array([v["x"], v["y"], v["z"]])


def velocity(v):
    return np.array([v["vx"], v["vy"], v["vz"]])


def compute_tca(obj1, obj2):
    """
    Compute Time of Closest Approach (seconds)
    """

    r1 = vector(obj1["position"])
    r2 = vector(obj2["position"])

    v1 = velocity(obj1["velocity"])
    v2 = velocity(obj2["velocity"])

    r = r2 - r1
    v = v2 - v1

    v_norm_sq = np.dot(v, v)

    if v_norm_sq == 0:
        return None

    tca = -np.dot(r, v) / v_norm_sq

    return max(0, tca)


def closest_distance(obj1, obj2, tca):
    """
    Compute distance at closest approach
    """

    r1 = vector(obj1["position"]) + velocity(obj1["velocity"]) * tca
    r2 = vector(obj2["position"]) + velocity(obj2["velocity"]) * tca

    return np.linalg.norm(r1 - r2) 