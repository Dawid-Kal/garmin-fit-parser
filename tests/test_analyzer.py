from unittest.mock import MagicMock, patch

import fitparse
import pandas as pd
import pytest

from analyzer import FitFileValidationError, RunnerProfile, TrainingAnalyzer


# =====================================================================
# RunnerProfile Unit Tests
# =====================================================================

@pytest.mark.parametrize(
    "time_str, expected_seconds",
    [
        ("0:19:30", 1170),
        ("1:02:05", 3725),
        ("0:00:01", 1),
        ("0:59:59", 3599),
        ("24:00:00", 86400),
        ("  0:19:30  ", 1170),
    ],
)
def test_parse_time_to_seconds_success(
    time_str: str, expected_seconds: int
) -> None:
    """Verify valid duration strings convert correctly to total seconds."""
    result = RunnerProfile.parse_time_to_seconds(time_str)
    assert result == expected_seconds


@pytest.mark.parametrize(
    "invalid_time_str",
    [
        "19:30",
        "1:2:3:4",
        "aa:bb:cc",
        "0:aa:00",
        "0:60:00",
        "0:00:65",
        "0:00:00",
        "-1:00:00",
        "0:-10:00",
    ],
)
def test_parse_time_to_seconds_raises_error(invalid_time_str: str) -> None:
    """Verify invalid duration formats raise ValueError with expected message."""
    expected_error_msg = "Invalid time format. Expected HH:MM:SS."

    with pytest.raises(ValueError, match=expected_error_msg):
        RunnerProfile.parse_time_to_seconds(invalid_time_str)


@pytest.mark.parametrize(
    "distance_meters, time_input, expected_profile",
    [
        # Elite profile threshold (Speed >= 5.21 m/s)
        (5000, "00:15:00", RunnerProfile(runner_profile="elite", max_jogging_speed=4.44)),
        # Semi-pro profile threshold (4.39 <= Speed < 5.21 m/s)
        (5000, "00:18:00", RunnerProfile(runner_profile="semi-pro", max_jogging_speed=4.00)),
        # Amateur profile threshold (Speed < 4.39 m/s)
        (5000, "00:25:00", RunnerProfile(runner_profile="amateur", max_jogging_speed=3.51)),
        # Boundary check: minimum allowed distance
        (1000, "00:03:00", RunnerProfile(runner_profile="elite", max_jogging_speed=4.44)),
        # Boundary check: maximum allowed distance
        (10000, "00:50:00", RunnerProfile(runner_profile="amateur", max_jogging_speed=3.51)),
    ],
)
def test_determine_runner_profile_valid_cases(
    distance_meters: int, time_input: str, expected_profile: RunnerProfile
) -> None:
    """Verify valid distances and times resolve to the correct RunnerProfile."""
    result = RunnerProfile.determine_runner_profile(distance_meters, time_input)
    assert result == expected_profile


def test_determine_runner_profile_missing_input() -> None:
    """Verify missing inputs safely fallback to the default amateur profile."""
    expected_fallback = RunnerProfile(runner_profile="amateur", max_jogging_speed=3.51)
    result = RunnerProfile.determine_runner_profile(None, None)
    assert result == expected_fallback


@pytest.mark.parametrize("invalid_distance", [999, 10001, 0, -5000])
def test_determine_runner_profile_invalid_distance_error(
    invalid_distance: int,
) -> None:
    """Verify distances outside the 1000-10000m range raise a business ValueError."""
    expected_error_msg = "Personal best distance must be between 1000 and 10000 meters."

    with pytest.raises(ValueError, match=expected_error_msg):
        RunnerProfile.determine_runner_profile(invalid_distance, "00:20:00")


def test_determine_runner_profile_bubbles_up_parser_exceptions() -> None:
    """Verify underlying time parser exceptions bubble up unmodified."""
    expected_error_msg = "Invalid time format. Expected HH:MM:SS."
    with pytest.raises(ValueError, match=expected_error_msg):
        RunnerProfile.determine_runner_profile(5000, "invalid-time-string")


# =====================================================================
# TrainingAnalyzer Unit & Mock Integration Tests
# =====================================================================

class MockFitField:
    """Mock container representing a data field inside a fitparse message."""

    def __init__(self, name: str, value: any) -> None:
        self.name = name
        self.value = value


class MockFitMessage:
    """Mock fitparse message object simulating 'record' or 'session' elements."""

    def __init__(self, name: str, data_dict: dict) -> None:
        self.name = name
        self._fields = [MockFitField(k, v) for k, v in data_dict.items()]

    def __iter__(self):
        return iter(self._fields)


@pytest.fixture
def analyzer() -> TrainingAnalyzer:
    """Provide a TrainingAnalyzer instance configured with an amateur profile."""
    mock_profile = RunnerProfile(runner_profile="amateur", max_jogging_speed=3.51)
    return TrainingAnalyzer(
        profile=mock_profile, file_path="tests/fixtures/sample_run.fit"
    )


@patch("fitparse.FitFile")
def test_process_and_clean_training_success(
    mock_fit_file_cls, analyzer
) -> None:
    """Verify processing pipeline extracts, cleans, and resamples to a 1s time grid."""
    mock_messages = [
        MockFitMessage("record", {"timestamp": "2026-07-08 10:00:00", "distance": 0.0, "enhanced_speed": 2.5}),
        MockFitMessage("record", {"timestamp": "2026-07-08 10:00:00", "distance": 0.0, "enhanced_speed": 2.5}),
        MockFitMessage("record", {"timestamp": "2026-07-08 10:00:02", "distance": 6.0, "enhanced_speed": 3.5}),
        MockFitMessage("session", {"total_timer_time": 2.0}),
    ]

    mock_instance = MagicMock()
    mock_instance.get_messages.return_value = mock_messages
    mock_fit_file_cls.return_value = mock_instance

    df_result = analyzer.process_and_clean_training()

    assert isinstance(df_result, pd.DataFrame)
    assert len(df_result) == 3
    assert {"timestamp", "distance", "enhanced_speed"}.issubset(df_result.columns)
    assert df_result.iloc[1]["distance"] == 0.0
    assert df_result.iloc[1]["enhanced_speed"] == 3.0


@patch("fitparse.FitFile")
def test_process_and_clean_training_missing_required_columns(
    mock_fit_file_cls, analyzer
) -> None:
    """Verify processing raises FitFileValidationError when required tracks are missing."""
    mock_messages = [
        MockFitMessage("record", {"timestamp": "2026-07-08 10:00:00", "distance": 0.0}),
        MockFitMessage("session", {"total_timer_time": 10.0}),
    ]

    mock_instance = MagicMock()
    mock_instance.get_messages.return_value = mock_messages
    mock_fit_file_cls.return_value = mock_instance

    with pytest.raises(FitFileValidationError, match="Plik FIT pochodzi ze starego urządzenia"):
        analyzer.process_and_clean_training()


@patch("fitparse.FitFile")
def test_process_and_clean_training_missing_session_summary(
    mock_fit_file_cls, analyzer
) -> None:
    """Verify processing raises FitFileValidationError when session summary is missing."""
    mock_messages = [
        MockFitMessage("record", {"timestamp": "2026-07-08 10:00:00", "distance": 0.0, "enhanced_speed": 2.0})
    ]

    mock_instance = MagicMock()
    mock_instance.get_messages.return_value = mock_messages
    mock_fit_file_cls.return_value = mock_instance

    with pytest.raises(FitFileValidationError, match="Plik FIT jest pusty lub nie zawiera podsumowania sesji"):
        analyzer.process_and_clean_training()


@patch("fitparse.FitFile")
def test_process_and_clean_training_handles_os_error(
    mock_fit_file_cls, analyzer
) -> None:
    """Verify I/O and file access issues map cleanly to a FitFileValidationError."""
    mock_fit_file_cls.side_effect = OSError("File unreadable or missing")

    with pytest.raises(FitFileValidationError, match="Nie można uzyskać dostępu do pliku na dysku"):
        analyzer.process_and_clean_training()


@patch("fitparse.FitFile")
def test_process_and_clean_training_handles_fit_parse_error(
    mock_fit_file_cls, analyzer
) -> None:
    """Verify corrupt binary structures safely map to a FitFileValidationError."""
    mock_fit_file_cls.side_effect = fitparse.FitParseError("Malformed binary payload")

    with pytest.raises(FitFileValidationError, match="Błąd krytyczny struktury pliku FIT"):
        analyzer.process_and_clean_training()