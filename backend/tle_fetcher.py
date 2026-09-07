import requests

TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"


def fetch_tle_data():

    headers = {
        "User-Agent": "Aegis-Orbital"
    }

    try:

        response = requests.get(
            TLE_URL,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        return response.text

    except requests.exceptions.RequestException as e:

        print("TLE download failed:", e)
        return ""