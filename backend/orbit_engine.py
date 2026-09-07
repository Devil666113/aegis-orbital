from sgp4.api import Satrec, jday
from datetime import datetime, UTC


def compute_satellite_position(satellite, current_time=None):

    sat = Satrec.twoline2rv(satellite.line1, satellite.line2)

    if current_time is None:
        current_time = datetime.now(UTC)

    jd, fr = jday(
        current_time.year,
        current_time.month,
        current_time.day,
        current_time.hour,
        current_time.minute,
        current_time.second
    )

    error_code, position, velocity = sat.sgp4(jd, fr)

    if error_code != 0:
        return None

    return {
        "name": satellite.name,
        "position": {
            "x": position[0],
            "y": position[1],
            "z": position[2]
        },
        "velocity": {
            "vx": velocity[0],
            "vy": velocity[1],
            "vz": velocity[2]
        }
    }