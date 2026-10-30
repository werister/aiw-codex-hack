"""Official wind rules. Runway 18 usability is inferred, never observed closure history."""

import json
import math
from datetime import timedelta
from pathlib import Path

RULES = json.loads(Path(__file__).with_name("rules.json").read_text(encoding="utf-8"))


def tailwind(speed, direction, heading):
    """Signed knots, positive behind the aircraft; unknown direction returns NaN."""
    if direction is None:
        return float("nan")
    return speed * math.cos(math.radians(direction - heading - 180))


def crosswind(speed, direction, heading):
    """Absolute crosswind component in knots."""
    if direction is None:
        return float("nan")
    return abs(speed * math.sin(math.radians(direction - heading)))


def r18_usable(speed, direction, gust=None):
    """Inferred weather usability; None means variable/unknown non-calm wind."""
    if not math.isfinite(speed) or speed < 0:
        return None
    peak = max(speed, gust) if gust is not None and math.isfinite(gust) else speed
    if direction is None or not math.isfinite(direction):
        if peak == 0:
            return True
        return None
    heading = RULES["runway_heading_deg"]["18"]
    return (tailwind(speed, direction, heading) < RULES["departure_tailwind_limit_kt"]
            and crosswind(peak, direction, heading) <= RULES["crosswind_limit_kt_incl_gusts"])


def od_state_machine(observations, initial_od="25", tailwind_since=None):
    """Return OD strings for ordered (time, direction, speed, gust) tuples.

    Samples describe wind at their timestamps. Do not backdate the first positive
    tailwind. Calm, variable or headwind resets the continuous-tailwind timer.
    """
    if initial_od not in ("25", "07"):
        raise ValueError("initial_od must be '25' or '07'")
    current = initial_od
    previous = None
    result = []
    for time, direction, speed, _gust in observations:
        if previous is not None and time <= previous:
            raise ValueError("wind timestamps must be strictly increasing")
        previous = time
        component = tailwind(speed, direction, RULES["runway_heading_deg"][current])
        if not math.isfinite(component) or speed <= 0 or component <= 1e-9:
            tailwind_since = None
        else:
            if tailwind_since is None:
                tailwind_since = time
            if (component >= RULES["landing_tailwind_change_now_kt"]
                    or time - tailwind_since > timedelta(minutes=RULES["landing_tailwind_tolerance_minutes"])):
                current = "07" if current == "25" else "25"
                tailwind_since = None
        result.append(current)
    return result
