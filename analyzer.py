from dataclasses import dataclass
import fitparse
import pandas as pd


@dataclass(frozen=True)
class RunnerProfile:
    """Immutable container for runner profile analysis results."""

    runner_profile: str
    max_jogging_speed: float

    @staticmethod
    def parse_time_to_seconds(time_str: str) -> int:
        """Convert HH:MM:SS duration string to total seconds.

        Internal helper for profile generation.
        """
        try:
            time_parts = time_str.strip().split(":")

            if len(time_parts) != 3:
                raise ValueError()

            hours = int(time_parts[0])
            minutes = int(time_parts[1])
            seconds = int(time_parts[2])

            total_seconds = (hours * 3600) + (minutes * 60) + seconds

            if (
                not (0 <= minutes < 60)
                or not (0 <= seconds < 60)
                or total_seconds <= 0
            ):
                raise ValueError()

            return total_seconds

        except ValueError:
            raise ValueError("Invalid time format. Expected HH:MM:SS.") from None

    @classmethod
    def determine_runner_profile(
        cls, distance_meters: int | None = None, time_input: str | None = None
    ) -> "RunnerProfile":
        """Factory method to determine runner profile based on personal best distance and time.

        Base criteria (calculated for a 5km reference distance):
        - Elite: < 16 min (speed >= 5.21 m/s) -> Cadence Lock: 3:45 min/km
        - Semi-pro: 16 - 19 min (speed >= 4.39 m/s) -> Cadence Lock: 4:15 min/km
        - Amateur: > 19 min (speed < 4.39 m/s) -> Cadence Lock: 4:45 min/km
        - Default fallback: Missing records default to amateur profile.
        """
        if distance_meters is None or time_input is None:
            return cls(runner_profile="amateur", max_jogging_speed=3.51)

        if not (1000 <= distance_meters <= 10000):
            raise ValueError(
                "Personal best distance must be between 1000 and 10000 meters."
            )

        time_seconds = cls.parse_time_to_seconds(time_input)
        pb_speed_mps = distance_meters / time_seconds

        if pb_speed_mps >= 5.21:
            return cls(runner_profile="elite", max_jogging_speed=4.44)

        if pb_speed_mps >= 4.39:
            return cls(runner_profile="semi-pro", max_jogging_speed=4.00)

        return cls(runner_profile="amateur", max_jogging_speed=3.51)


class FitFileValidationError(Exception):
    """Raised when a FIT file is corrupt, empty, or lacks required modern metrics."""
    pass


class TrainingAnalyzer:
    """Handles loading, cleaning, and structural normalization of FIT files."""

    def __init__(self, profile: RunnerProfile, file_path: str) -> None:
        self.profile = profile
        self.file_path = file_path
        self.df: pd.DataFrame | None = None

    def process_and_clean_training(self) -> pd.DataFrame:
        """Load FIT activity files, clean records, and build a regularized 1Hz time grid."""
        # Stage 1: Extraction via fitparse
        try:
            fit_file = fitparse.FitFile(self.file_path)
            records_list = []
            official_duration = None

            for message in fit_file.get_messages():
                if message.name == "record":
                    data_dict = {}
                    for data in message:
                        if data.name in [
                            "timestamp",
                            "distance",
                            "enhanced_speed",
                            "heart_rate",
                            "cadence"
                        ]:
                            data_dict[data.name] = data.value
                    if data_dict:
                        records_list.append(data_dict)
                elif message.name == "session":
                    for data in message:
                        if data.name == "total_timer_time":
                            official_duration = data.value

        except OSError as e:
            raise FitFileValidationError(
                f"Nie można uzyskać dostępu do pliku na dysku: {e}"
            ) from e

        except (fitparse.FitParseError, AttributeError) as e:
            raise FitFileValidationError(
                f"Błąd krytyczny struktury pliku FIT: {e}"
            ) from e

        if not records_list or official_duration is None:
            raise FitFileValidationError(
                "Plik FIT jest pusty lub nie zawiera podsumowania sesji."
            )

        # Stage 2: Transformation and filtering via Pandas
        try:
            self.df = pd.DataFrame(records_list)

            required_columns = {"timestamp", "distance", "enhanced_speed"}
            if not required_columns.issubset(self.df.columns):
                raise FitFileValidationError(
                    "Plik FIT pochodzi ze starego urządzenia. "
                    f"Brakuje kolumn: {required_columns - set(self.df.columns)}"
                )

            self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])
            self.df = self.df.drop_duplicates(subset=["timestamp"], keep="first")
            self.df = self.df.sort_values(by="timestamp").reset_index(drop=True)

            # TODO: training_date_str = self.df["timestamp"].iat[0].strftime("%Y-%m-%d")

            self.df = self.df.set_index("timestamp").resample("1s").asfreq()
            self.df["distance"] = self.df["distance"].ffill()
            self.df["enhanced_speed"] = (
                self.df["enhanced_speed"]
                .interpolate(method="linear")
                .ffill()
                .bfill()
            )
            self.df = self.df.reset_index()

            return self.df

        except (ValueError, TypeError) as e:
            raise FitFileValidationError(
                f"Niepoprawny format danych wewnątrz pliku FIT: {e}"
            ) from e