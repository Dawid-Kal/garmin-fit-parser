import pytest

from analyzer import TrainingAnalyzer, RunnerProfile


@pytest.fixture
def analyzer():
    """Provide a fresh instance of TrainingAnalyzer for each test."""
    return TrainingAnalyzer("tests/fixtures/sample_run.fit")


@pytest.mark.parametrize(
    "time_str, expected_seconds",
    [
        ("0:19:30", 1170),
        ("1:02:05", 3725),
        ("0:00:01", 1),
        ("0:59:59", 3599),
        ("24:00:00", 86400),
        ("  0:19:30  ", 1170),  # Verifies whitespace stripping
    ]
)
def test_parse_time_to_seconds_success(
    analyzer: TrainingAnalyzer,
    time_str: str, 
    expected_seconds: int
) -> None:
    """Test that valid time formats and edge cases convert correctly to seconds."""
    result = analyzer.parse_time_to_seconds(time_str)
    assert result == expected_seconds


@pytest.mark.parametrize(
    "invalid_time_str",
    [
        "19:30",     # Missing hours segment (IndexError trigger)
        "1:2:3:4",   # Redundant segments
        "aa:bb:cc",  # Non-numeric input
        "0:aa:00",   # Mixed invalid input
        "0:60:00",   # Invalid minutes value
        "0:00:65",   # Invalid seconds value
        "0:00:00",   # Zero duration boundary
        "-1:00:00",  # Negative duration boundary
        "0:-10:00",
    ]
)
def test_parse_time_to_seconds_raises_error(
    analyzer: TrainingAnalyzer, 
    invalid_time_str: str
) -> None:
    """Test that invalid inputs raise ValueError with a matching user-facing message."""
    expected_error_msg = "Invalid time format. Expected HH:MM:SS."
    
    with pytest.raises(ValueError) as exc_info:
        analyzer.parse_time_to_seconds(invalid_time_str)
        
    assert str(exc_info.value) == expected_error_msg


@pytest.mark.parametrize(
    "distance_meters, time_input, expected_profile",
    [
        # Case 1: Elite profile threshold (Speed >= 5.21 m/s)
        # 5000m / 900s (15:00) = 5.55 m/s
        (5000, "00:15:00", RunnerProfile(runner_profile="elite", max_jogging_speed=4.44)),
        
        # Case 2: Semi-pro profile threshold (4.39 <= Speed < 5.21 m/s)
        # 5000m / 1080s (18:00) = 4.63 m/s
        (5000, "00:18:00", RunnerProfile(runner_profile="semi-pro", max_jogging_speed=4.00)),
        
        # Case 3: Amateur profile threshold (Speed < 4.39 m/s)
        # 5000m / 1500s (25:00) = 3.33 m/s
        (5000, "00:25:00", RunnerProfile(runner_profile="amateur", max_jogging_speed=3.51)),
        
        # Case 4: Boundary check - exact minimum allowed distance (1000m)
        # 1000m / 180s (03:00) = 5.55 m/s -> Elite
        (1000, "00:03:00", RunnerProfile(runner_profile="elite", max_jogging_speed=4.44)),
        
        # Case 5: Boundary check - exact maximum allowed distance (10000m)
        # 10000m / 3000s (50:00) = 3.33 m/s -> Amateur
        (10000, "00:50:00", RunnerProfile(runner_profile="amateur", max_jogging_speed=3.51)),
    ]
)
def test_determine_runner_profile_valid_cases(
    analyzer: TrainingAnalyzer,
    distance_meters: int,
    time_input: str,
    expected_profile: RunnerProfile
) -> None:
    """Verify that valid distances and times correctly resolve to the expected RunnerProfile."""
    result = analyzer.determine_runner_profile(distance_meters, time_input)
    assert result == expected_profile


def test_determine_runner_profile_missing_input(analyzer: TrainingAnalyzer) -> None:
    """Verify that missing inputs fallback safely to the default amateur profile."""
    expected_fallback = RunnerProfile(runner_profile="amateur", max_jogging_speed=3.51)
    result = analyzer.determine_runner_profile(None, None)
    assert result == expected_fallback


@pytest.mark.parametrize(
    "invalid_distance",
    [999, 10001, 0, -5000]
)
def test_determine_runner_profile_invalid_distance_raises_value_error(
    analyzer: TrainingAnalyzer,
    invalid_distance: int
) -> None:
    """Verify that distances outside the 1000-10000m range raise a business-specific ValueError."""
    expected_error_msg = "Personal best distance must be between 1000 and 10000 meters."
    
    with pytest.raises(ValueError, match=expected_error_msg):
        analyzer.determine_runner_profile(invalid_distance, "00:20:00")


def test_determine_runner_profile_bubbles_up_parser_exceptions(analyzer: TrainingAnalyzer) -> None:
    """Verify that underlying time parser exceptions are correctly bubbled up."""
    with pytest.raises(ValueError, match="Invalid time format. Expected HH:MM:SS."):
        analyzer.determine_runner_profile(5000, "invalid-time-string")
