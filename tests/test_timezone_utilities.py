"""Tests for timezone utility functions."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from efts_io.conventions import detect_timezone_info, extract_utc_offset_string, validate_fixed_offset_timezone


class TestDetectTimezoneInfo:
    """Tests for detect_timezone_info() function."""

    def test_timezone_naive_datetimeindex(self):
        """Test that timezone-naive DatetimeIndex returns UTC."""
        timestamps = pd.date_range("2024-01-01", periods=3)
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_utc_datetimeindex(self):
        """Test that UTC DatetimeIndex returns UTC."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_utc_alias_gmt(self):
        """Test that GMT is normalized to UTC."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="GMT")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_utc_alias_etc_utc(self):
        """Test that Etc/UTC is normalized to UTC."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="Etc/UTC")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_fixed_offset_positive(self):
        """Test fixed offset positive timezone (UTC+10:00)."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC+10:00")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC+10:00"
        assert offset_string == "+10:00"

    def test_fixed_offset_negative(self):
        """Test fixed offset negative timezone (UTC-05:00)."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC-05:00")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC-05:00"
        assert offset_string == "-05:00"

    def test_fixed_offset_non_hour(self):
        """Test fixed offset with non-hour offset (UTC+05:30)."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC+05:30")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC+05:30"
        assert offset_string == "+05:30"

    def test_fixed_offset_45_minutes(self):
        """Test fixed offset with 45-minute offset (UTC+05:45)."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC+05:45")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC+05:45"
        assert offset_string == "+05:45"

    def test_fixed_offset_edge_case_positive(self):
        """Test edge case maximum offset (UTC+14:00)."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC+14:00")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC+14:00"
        assert offset_string == "+14:00"

    def test_fixed_offset_edge_case_negative(self):
        """Test edge case minimum offset (UTC-12:00)."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC-12:00")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC-12:00"
        assert offset_string == "-12:00"

    def test_single_timestamp_naive(self):
        """Test single timezone-naive Timestamp."""
        ts = pd.Timestamp("2024-01-01")
        tz_string, offset_string = detect_timezone_info(ts)
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_single_timestamp_with_tz(self):
        """Test single timezone-aware Timestamp."""
        ts = pd.Timestamp("2024-01-01", tz="UTC+10:00")
        tz_string, offset_string = detect_timezone_info(ts)
        assert tz_string == "UTC+10:00"
        assert offset_string == "+10:00"

    def test_list_of_timestamps(self):
        """Test list of Timestamps."""
        timestamps = [
            pd.Timestamp("2024-01-01", tz="UTC+10:00"),
            pd.Timestamp("2024-01-02", tz="UTC+10:00"),
        ]
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "UTC+10:00"
        assert offset_string == "+10:00"

    def test_string_timestamp(self):
        """Test string timestamp (becomes naive)."""
        tz_string, offset_string = detect_timezone_info("2024-01-01")
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_datetime_timestamp_naive(self):
        """Test datetime.datetime timestamp (naive)."""
        dt = datetime(2024, 1, 1)
        tz_string, offset_string = detect_timezone_info(dt)
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_numpy_datetime64(self):
        """Test numpy.datetime64 timestamp."""
        dt = np.datetime64("2024-01-01")
        tz_string, offset_string = detect_timezone_info(dt)
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_empty_datetimeindex_raises(self):
        """Test that empty DatetimeIndex raises ValueError."""
        timestamps = pd.DatetimeIndex([])
        with pytest.raises(ValueError, match="Cannot detect timezone from empty"):
            detect_timezone_info(timestamps)

    def test_empty_list_raises(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="Cannot detect timezone from empty"):
            detect_timezone_info([])

    def test_invalid_type_raises(self):
        """Test that invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Cannot detect timezone from type"):
            detect_timezone_info(123)

    def test_named_timezone_dst(self):
        """Test named timezone (will be handled in later steps, but test detection works)."""
        # For now, just verify we can detect the timezone string and offset
        # Note: The offset will be based on the specific date
        timestamps = pd.date_range("2024-01-01", periods=3, tz="US/Eastern")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "US/Eastern"
        # In January, US/Eastern is UTC-05:00 (standard time)
        assert offset_string == "-05:00"

    def test_named_timezone_dst_summer(self):
        """Test named timezone in summer (DST active)."""
        # In July, US/Eastern is UTC-04:00 (daylight saving time)
        timestamps = pd.date_range("2024-07-01", periods=3, tz="US/Eastern")
        tz_string, offset_string = detect_timezone_info(timestamps)
        assert tz_string == "US/Eastern"
        # Note: This will be -04:00 due to DST
        assert offset_string == "-04:00"


class TestValidateFixedOffsetTimezone:
    """Tests for validate_fixed_offset_timezone() function."""

    def test_utc_alias_normalized(self):
        """Test that UTC is recognized and normalized."""
        tz_string, offset_string = validate_fixed_offset_timezone("UTC")
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_gmt_alias_normalized(self):
        """Test that GMT is normalized to UTC."""
        tz_string, offset_string = validate_fixed_offset_timezone("GMT")
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_etc_utc_alias_normalized(self):
        """Test that Etc/UTC is normalized to UTC."""
        tz_string, offset_string = validate_fixed_offset_timezone("Etc/UTC")
        assert tz_string == "UTC"
        assert offset_string == "+00:00"

    def test_fixed_offset_positive(self):
        """Test fixed offset positive timezone is accepted."""
        tz_string, offset_string = validate_fixed_offset_timezone("UTC+10:00")
        assert tz_string == "UTC+10:00"
        assert offset_string == "+10:00"

    def test_fixed_offset_negative(self):
        """Test fixed offset negative timezone is accepted."""
        tz_string, offset_string = validate_fixed_offset_timezone("UTC-05:00")
        assert tz_string == "UTC-05:00"
        assert offset_string == "-05:00"

    def test_fixed_offset_non_hour(self):
        """Test fixed offset with non-hour offset is accepted."""
        tz_string, offset_string = validate_fixed_offset_timezone("UTC+05:30")
        assert tz_string == "UTC+05:30"
        assert offset_string == "+05:30"

    def test_fixed_offset_45_minutes(self):
        """Test fixed offset with 45-minute offset is accepted."""
        tz_string, offset_string = validate_fixed_offset_timezone("UTC+05:45")
        assert tz_string == "UTC+05:45"
        assert offset_string == "+05:45"

    def test_fixed_offset_edge_case_positive(self):
        """Test edge case maximum offset is accepted."""
        tz_string, offset_string = validate_fixed_offset_timezone("UTC+14:00")
        assert tz_string == "UTC+14:00"
        assert offset_string == "+14:00"

    def test_fixed_offset_edge_case_negative(self):
        """Test edge case minimum offset is accepted."""
        tz_string, offset_string = validate_fixed_offset_timezone("UTC-12:00")
        assert tz_string == "UTC-12:00"
        assert offset_string == "-12:00"

    def test_dst_timezone_us_eastern_rejected(self):
        """Test that US/Eastern (DST) is rejected."""
        with pytest.raises(NotImplementedError) as exc_info:
            validate_fixed_offset_timezone("US/Eastern")
        error_msg = str(exc_info.value).lower()
        assert "daylight saving" in error_msg or "dst" in error_msg
        assert "us/eastern" in error_msg.lower()
        assert "fixed utc offset" in error_msg or "fixed offset" in error_msg

    def test_dst_timezone_us_pacific_rejected(self):
        """Test that US/Pacific (DST) is rejected."""
        with pytest.raises(NotImplementedError) as exc_info:
            validate_fixed_offset_timezone("US/Pacific")
        error_msg = str(exc_info.value).lower()
        assert "daylight saving" in error_msg or "dst" in error_msg

    def test_dst_timezone_europe_london_rejected(self):
        """Test that Europe/London (DST) is rejected."""
        with pytest.raises(NotImplementedError) as exc_info:
            validate_fixed_offset_timezone("Europe/London")
        error_msg = str(exc_info.value).lower()
        assert "daylight saving" in error_msg or "dst" in error_msg

    def test_dst_timezone_australia_sydney_rejected(self):
        """Test that Australia/Sydney (DST) is rejected."""
        with pytest.raises(NotImplementedError) as exc_info:
            validate_fixed_offset_timezone("Australia/Sydney")
        error_msg = str(exc_info.value).lower()
        assert "daylight saving" in error_msg or "dst" in error_msg

    def test_dst_timezone_america_new_york_rejected(self):
        """Test that America/New_York (DST) is rejected."""
        with pytest.raises(NotImplementedError) as exc_info:
            validate_fixed_offset_timezone("America/New_York")
        error_msg = str(exc_info.value).lower()
        assert "daylight saving" in error_msg or "dst" in error_msg

    def test_invalid_timezone_string_raises(self):
        """Test that invalid timezone string raises ValueError."""
        with pytest.raises(ValueError, match="Could not parse timezone"):
            validate_fixed_offset_timezone("Invalid/Timezone")

    def test_malformed_timezone_string_raises(self):
        """Test that malformed timezone string raises ValueError."""
        with pytest.raises(ValueError):
            validate_fixed_offset_timezone("UTC+99:99")

    def test_with_sample_timestamp(self):
        """Test validation with explicit sample timestamp."""
        sample = pd.Timestamp("2024-06-15 12:00:00")
        tz_string, offset_string = validate_fixed_offset_timezone("UTC+10:00", sample_timestamp=sample)
        assert tz_string == "UTC+10:00"
        assert offset_string == "+10:00"

    def test_dst_error_message_is_helpful(self):
        """Test that DST error message provides helpful guidance."""
        with pytest.raises(NotImplementedError) as exc_info:
            validate_fixed_offset_timezone("US/Eastern")
        error_msg = str(exc_info.value)
        # Check for key parts of the helpful error message
        assert "daylight saving" in error_msg.lower() or "DST" in error_msg
        assert "not supported" in error_msg
        assert "fixed UTC offset" in error_msg or "fixed offset" in error_msg
        assert "UTC+10:00" in error_msg or "UTC-05:00" in error_msg  # Example suggestions
        assert "STF2" in error_msg or "NetCDF" in error_msg  # Context

    def test_fixed_offset_various_formats(self):
        """Test that various fixed offset formats are accepted."""
        test_cases = [
            ("UTC+01:00", "+01:00"),
            ("UTC+02:00", "+02:00"),
            ("UTC+09:30", "+09:30"),
            ("UTC-03:00", "-03:00"),
            ("UTC-08:00", "-08:00"),
        ]
        for tz_input, expected_offset in test_cases:
            tz_string, offset_string = validate_fixed_offset_timezone(tz_input)
            assert tz_string == tz_input
            assert offset_string == expected_offset


class TestExtractUtcOffsetString:
    """Tests for extract_utc_offset_string() function."""

    def test_datetimeindex_utc(self):
        """Test extracting offset from UTC DatetimeIndex."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC")
        offset = extract_utc_offset_string(timestamps)
        assert offset == "+00:00"

    def test_datetimeindex_positive_offset(self):
        """Test extracting positive offset from DatetimeIndex."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC+10:00")
        offset = extract_utc_offset_string(timestamps)
        assert offset == "+10:00"

    def test_datetimeindex_negative_offset(self):
        """Test extracting negative offset from DatetimeIndex."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC-05:00")
        offset = extract_utc_offset_string(timestamps)
        assert offset == "-05:00"

    def test_datetimeindex_non_hour_offset(self):
        """Test extracting non-hour offset from DatetimeIndex."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC+05:30")
        offset = extract_utc_offset_string(timestamps)
        assert offset == "+05:30"

    def test_datetimeindex_45_minute_offset(self):
        """Test extracting 45-minute offset from DatetimeIndex."""
        timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC+05:45")
        offset = extract_utc_offset_string(timestamps)
        assert offset == "+05:45"

    def test_timestamp_utc(self):
        """Test extracting offset from UTC Timestamp."""
        ts = pd.Timestamp("2024-01-01", tz="UTC")
        offset = extract_utc_offset_string(ts)
        assert offset == "+00:00"

    def test_timestamp_positive_offset(self):
        """Test extracting positive offset from Timestamp."""
        ts = pd.Timestamp("2024-01-01", tz="UTC+10:00")
        offset = extract_utc_offset_string(ts)
        assert offset == "+10:00"

    def test_timestamp_negative_offset(self):
        """Test extracting negative offset from Timestamp."""
        ts = pd.Timestamp("2024-01-01", tz="UTC-05:00")
        offset = extract_utc_offset_string(ts)
        assert offset == "-05:00"

    def test_timezone_string_utc(self):
        """Test extracting offset from UTC string."""
        offset = extract_utc_offset_string("UTC")
        assert offset == "+00:00"

    def test_timezone_string_positive_offset(self):
        """Test extracting offset from positive offset string."""
        offset = extract_utc_offset_string("UTC+10:00")
        assert offset == "+10:00"

    def test_timezone_string_negative_offset(self):
        """Test extracting offset from negative offset string."""
        offset = extract_utc_offset_string("UTC-05:00")
        assert offset == "-05:00"

    def test_timezone_string_non_hour_offset(self):
        """Test extracting non-hour offset from string."""
        offset = extract_utc_offset_string("UTC+05:30")
        assert offset == "+05:30"

    def test_edge_case_positive_max(self):
        """Test maximum positive offset."""
        offset = extract_utc_offset_string("UTC+14:00")
        assert offset == "+14:00"

    def test_edge_case_negative_max(self):
        """Test maximum negative offset."""
        offset = extract_utc_offset_string("UTC-12:00")
        assert offset == "-12:00"

    def test_timezone_naive_datetimeindex_raises(self):
        """Test that timezone-naive DatetimeIndex raises ValueError."""
        timestamps = pd.date_range("2024-01-01", periods=3)
        with pytest.raises(ValueError, match="timezone-naive"):
            extract_utc_offset_string(timestamps)

    def test_timezone_naive_timestamp_raises(self):
        """Test that timezone-naive Timestamp raises ValueError."""
        ts = pd.Timestamp("2024-01-01")
        with pytest.raises(ValueError, match="timezone-naive"):
            extract_utc_offset_string(ts)

    def test_empty_datetimeindex_raises(self):
        """Test that empty DatetimeIndex raises ValueError."""
        timestamps = pd.DatetimeIndex([])
        with pytest.raises(ValueError, match="empty"):
            extract_utc_offset_string(timestamps)

    def test_invalid_timezone_string_raises(self):
        """Test that invalid timezone string raises ValueError."""
        with pytest.raises(ValueError, match="Could not extract offset"):
            extract_utc_offset_string("Invalid/Timezone")

    def test_invalid_type_raises(self):
        """Test that invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Cannot extract UTC offset from type"):
            extract_utc_offset_string(123)

    def test_timezone_object_from_string(self):
        """Test extracting offset from timezone object created from string."""
        # Create a timezone object and test extraction
        ts = pd.Timestamp("2024-01-01", tz="UTC+10:00")
        tz_obj = ts.tz
        offset = extract_utc_offset_string(tz_obj)
        assert offset == "+10:00"

    def test_various_offsets(self):
        """Test various offset values are formatted correctly."""
        test_cases = [
            ("UTC+00:00", "+00:00"),
            ("UTC+01:00", "+01:00"),
            ("UTC+02:00", "+02:00"),
            ("UTC+03:00", "+03:00"),
            ("UTC+04:00", "+04:00"),
            ("UTC+09:30", "+09:30"),
            ("UTC-01:00", "-01:00"),
            ("UTC-02:00", "-02:00"),
            ("UTC-03:00", "-03:00"),
            ("UTC-04:00", "-04:00"),
            ("UTC-08:00", "-08:00"),
        ]
        for tz_string, expected_offset in test_cases:
            offset = extract_utc_offset_string(tz_string)
            assert offset == expected_offset, f"Failed for {tz_string}"

    def test_consistency_with_detect_timezone_info(self):
        """Test that results are consistent with detect_timezone_info."""
        test_timezones = ["UTC", "UTC+10:00", "UTC-05:00", "UTC+05:30"]
        for tz_str in test_timezones:
            timestamps = pd.date_range("2024-01-01", periods=3, tz=tz_str)
            # Get offset from extract_utc_offset_string
            offset1 = extract_utc_offset_string(timestamps)
            # Get offset from detect_timezone_info
            _, offset2 = detect_timezone_info(timestamps)
            assert offset1 == offset2, f"Inconsistent results for {tz_str}"
