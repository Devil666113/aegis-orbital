"""
TLE Parser Module
Aegis Orbital

Purpose:
Convert raw TLE text data into structured Satellite objects
that can be used by the orbit engine.
"""

class Satellite:
    """
    Satellite object representing one orbital body.
    """

    def __init__(self, name, line1, line2):
        self.name = name
        self.line1 = line1
        self.line2 = line2

    def to_dict(self):
        """
        Convert satellite object to dictionary
        (useful later for APIs).
        """
        return {
            "name": self.name,
            "line1": self.line1,
            "line2": self.line2
        }

    def __repr__(self):
        return f"Satellite(name={self.name})"


def parse_tle_data(raw_data):
    """
    Parse raw TLE text into Satellite objects.

    Parameters:
        raw_data (str): raw text downloaded from TLE source

    Returns:
        list: list of Satellite objects
    """

    satellites = []

    # Split raw text into lines
    lines = raw_data.strip().split("\n")

    # Process every 3 lines
    for i in range(0, len(lines), 3):

        # Prevent index errors
        if i + 2 >= len(lines):
            break

        name = lines[i].strip()
        line1 = lines[i + 1].strip()
        line2 = lines[i + 2].strip()

        # Basic validation of TLE format
        if not line1.startswith("1") or not line2.startswith("2"):
            continue

        sat = Satellite(name, line1, line2)
        satellites.append(sat)

    return satellites


