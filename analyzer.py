from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class RunnerProfile:
    """Immutable container for runner profile analysis results."""

    runner_profile: str
    max_jogging_speed: float


class TrainingAnalyzer:

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.df: pd.DataFrame | None = None

    def parse_time_to_seconds(self, time_str: str) -> int:
        """Convert HH:MM:SS duration string to total seconds."""
        try:
            time_parts = time_str.strip().split(":")

            if len(time_parts) != 3:
                raise ValueError()

            hours = int(time_parts[0])
            minutes = int(time_parts[1])
            seconds = int(time_parts[2])

            total_seconds = (hours * 3600) + (minutes * 60) + seconds

            if not (0 <= minutes < 60) or not (0 <= seconds < 60) or total_seconds <= 0:
                raise ValueError()

            return total_seconds

        except ValueError:
            raise ValueError("Invalid time format. Expected HH:MM:SS.")

    def determine_runner_profile(
        self, distance_meters: int | None = None, time_input: str | None = None
    ) -> RunnerProfile:
        """Determine runner profile based on personal best distance and time.

        Base criteria (calculated for a 5km reference distance):
        - Elite: < 16 min (speed >= 5.21 m/s) -> Cadence Lock: 3:45 min/km
        - Semi-pro: 16 - 19 min (speed >= 4.39 m/s) -> Cadence Lock: 4:15 min/km
        - Amateur: > 19 min (speed < 4.39 m/s) -> Cadence Lock: 4:45 min/km
        - Default fallback: Missing records default to amateur profile.
        """
        if distance_meters is None or time_input is None:
            return RunnerProfile(runner_profile="amateur", max_jogging_speed=3.51)

        if not (1000 <= distance_meters <= 10000):
            raise ValueError(
                "Personal best distance must be between 1000 and 10000 meters."
            )

        time_seconds = self.parse_time_to_seconds(time_input)
        pb_speed_mps = distance_meters / time_seconds

        if pb_speed_mps >= 5.21:
            return RunnerProfile(runner_profile="elite", max_jogging_speed=4.44)

        if pb_speed_mps >= 4.39:
            return RunnerProfile(runner_profile="semi-pro", max_jogging_speed=4.00)

        return RunnerProfile(runner_profile="amateur", max_jogging_speed=3.51)