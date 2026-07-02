import pandas as pd

class TrainingAnalyzer:

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.df: "pd.DataFrame | None" = None

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

            if minutes >= 60 or seconds >= 60 or total_seconds <= 0:
                raise ValueError()
            
            return int(total_seconds)
            
        except ValueError:
            raise ValueError("Invalid time format. Expected HH:MM:SS.")
