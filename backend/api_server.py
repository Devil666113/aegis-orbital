from fastapi import FastAPI
from tle_fetcher import fetch_tle_data
from tle_parser import parse_tle_data
from position_generator import generate_positions
from collision_detection import detect_collisions

app = FastAPI()

# Load once at startup
raw_data = fetch_tle_data()
satellites = parse_tle_data(raw_data)
satellites = satellites[:200]


@app.get("/data")
def get_data():

    positions = generate_positions(satellites, debris_count=5)
    collisions = detect_collisions(positions)

    return {
        "positions": positions,
        "collisions": collisions
    }