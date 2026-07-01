import pytest

from analyzer import TrainingAnalyzer


@pytest.fixture
def analyzer():
    """Provide a fresh instance of TrainingAnalyzer for each test."""
    return TrainingAnalyzer("Trening.fit")


@pytest.mark.parametrize(
    "time_str, expected_seconds",
    [
        ("0:19:30", 1170.0),
        ("1:02:05", 3725.0),
        ("0:00:01", 1.0),
        ("0:59:59", 3599.0),
        ("24:00:00", 86400.0),
        ("  0:19:30  ", 1170.0),  # Verifies whitespace stripping
    ]
)
def test_parse_time_to_seconds_success(analyzer, time_str, expected_seconds):
    """Test that valid time formats and edge cases convert correctly to seconds."""
    assert analyzer.parse_time_to_seconds(time_str) == expected_seconds


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
    ]
)
def test_parse_time_to_seconds_raises_error(analyzer, invalid_time_str):
    """Test that invalid inputs raise ValueError with a matching user-facing message."""
    expected_error_msg = "Invalid time format. Expected HH:MM:SS."
    
    with pytest.raises(ValueError) as exc_info:
        analyzer.parse_time_to_seconds(invalid_time_str)
        
    assert str(exc_info.value) == expected_error_msg