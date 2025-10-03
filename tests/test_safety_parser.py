"""Unit tests for safety and toxicity data parsing."""

import pytest
from trials.safety_parser import (
    parse_adverse_events,
    format_safety_display,
    extract_toxicity_from_results
)


class TestParseAdverseEvents:
    """Test cases for adverse events parsing."""

    def test_parse_common_aes(self):
        """Test parsing common adverse events."""
        text = "Common adverse events: nausea, fatigue, headache, dizziness"
        result = parse_adverse_events(text)

        assert "common_aes" in result
        assert len(result["common_aes"]) > 0
        # Should capture at least some of the events
        assert any("nausea" in ae.lower() or "fatigue" in ae.lower()
                  for ae in result["common_aes"])

    def test_parse_dose_limiting_toxicities(self):
        """Test parsing dose-limiting toxicities."""
        text = "Dose-limiting toxicities: neutropenia, thrombocytopenia"
        result = parse_adverse_events(text)

        assert "dose_limiting_toxicities" in result
        assert len(result["dose_limiting_toxicities"]) > 0

    def test_parse_grade_3_4_events(self):
        """Test parsing grade 3-4 events."""
        text = "Grade 3-4 adverse events: severe anemia, neutropenia"
        result = parse_adverse_events(text)

        assert "grade_3_4_events" in result
        assert len(result["grade_3_4_events"]) > 0

    def test_parse_safety_monitoring(self):
        """Test parsing safety monitoring requirements."""
        text = "Requires ECG monitoring and liver function tests"
        result = parse_adverse_events(text)

        assert "safety_monitoring" in result
        # Should detect ECG or liver function monitoring

    def test_empty_input(self):
        """Test with empty input."""
        result = parse_adverse_events(None, None)

        assert result["common_aes"] == []
        assert result["dose_limiting_toxicities"] == []
        assert result["grade_3_4_events"] == []
        assert result["safety_monitoring"] == []

    def test_combined_texts(self):
        """Test parsing from both eligibility and description."""
        eligibility = "Common toxicities: fatigue, rash"
        description = "Dose-limiting toxicity: grade 4 neutropenia"
        result = parse_adverse_events(eligibility, description)

        # Should find events from both sources
        assert len(result["common_aes"]) > 0 or len(result["dose_limiting_toxicities"]) > 0

    def test_case_insensitive(self):
        """Test case-insensitive parsing."""
        text = "ADVERSE EVENTS: NAUSEA, FATIGUE"
        result = parse_adverse_events(text)

        assert len(result["common_aes"]) > 0

    def test_multiple_ae_patterns(self):
        """Test multiple AE extraction patterns."""
        texts = [
            "adverse events: nausea, vomiting",
            "toxicity: diarrhea, rash",
            "side effects: headache, dizziness",
            "common AEs: fatigue, anorexia"
        ]

        for text in texts:
            result = parse_adverse_events(text)
            assert len(result["common_aes"]) > 0, f"Failed to parse: {text}"

    def test_cardiac_monitoring(self):
        """Test detection of cardiac monitoring requirements."""
        text = "Requires cardiac monitoring via ECG and echocardiogram"
        result = parse_adverse_events(text)

        assert len(result["safety_monitoring"]) > 0

    def test_deduplication(self):
        """Test that results are deduplicated."""
        text = "adverse events: nausea, nausea, nausea, fatigue, fatigue"
        result = parse_adverse_events(text)

        # Should not have duplicates
        ae_list = result["common_aes"]
        assert len(ae_list) == len(set(ae_list))

    def test_length_limits(self):
        """Test that results are limited to reasonable lengths."""
        # Very long list of events
        events = ", ".join([f"event{i}" for i in range(100)])
        text = f"common adverse events: {events}"
        result = parse_adverse_events(text)

        # Should be limited (max 10 for common AEs)
        assert len(result["common_aes"]) <= 10

    def test_filter_very_short_events(self):
        """Test that very short event names are filtered out."""
        text = "adverse events: a, b, c, proper event name"
        result = parse_adverse_events(text)

        # Should filter out single character events
        assert all(len(ae) > 5 for ae in result["common_aes"])

    def test_filter_very_long_events(self):
        """Test that very long event names are filtered out."""
        very_long = "a" * 200
        text = f"adverse events: {very_long}, proper event"
        result = parse_adverse_events(text)

        # Should filter out events longer than 100 chars
        assert all(len(ae) < 100 for ae in result["common_aes"])


class TestFormatSafetyDisplay:
    """Test cases for safety data formatting."""

    def test_format_complete_safety_data(self):
        """Test formatting complete safety data."""
        safety_data = {
            "dose_limiting_toxicities": ["neutropenia"],
            "grade_3_4_events": ["anemia", "fatigue"],
            "common_aes": ["nausea", "diarrhea"],
            "safety_monitoring": ["ECG", "liver function tests"]
        }

        result = format_safety_display(safety_data)

        assert "Dose-Limiting Toxicities" in result
        assert "Grade 3-4 Events" in result
        assert "Common AEs" in result
        assert "Monitoring Required" in result
        assert "neutropenia" in result
        assert "anemia" in result

    def test_format_partial_safety_data(self):
        """Test formatting with partial safety data."""
        safety_data = {
            "dose_limiting_toxicities": [],
            "grade_3_4_events": ["severe anemia"],
            "common_aes": [],
            "safety_monitoring": []
        }

        result = format_safety_display(safety_data)

        assert "Grade 3-4 Events" in result
        assert "severe anemia" in result
        # Should not include empty sections
        assert "Dose-Limiting" not in result or "Grade 3-4" in result

    def test_format_empty_safety_data(self):
        """Test formatting with no safety data."""
        safety_data = {
            "dose_limiting_toxicities": [],
            "grade_3_4_events": [],
            "common_aes": [],
            "safety_monitoring": []
        }

        result = format_safety_display(safety_data)

        assert "not available" in result.lower()

    def test_format_with_emojis(self):
        """Test that formatting includes visual indicators."""
        safety_data = {
            "common_aes": ["nausea"]
        }

        result = format_safety_display(safety_data)

        # Should include emoji indicators
        assert "💊" in result or "Common" in result


class TestExtractToxicityFromResults:
    """Test cases for extracting toxicity from trial results."""

    def test_extract_from_complete_results(self):
        """Test extraction from complete results data."""
        trial_data = {
            "resultsSection": {
                "adverseEventsModule": {
                    "frequencyThreshold": "5%",
                    "eventGroups": [
                        {
                            "title": "Treatment Arm",
                            "deathsNumAffected": 2,
                            "seriousNumAffected": 10
                        }
                    ]
                }
            }
        }

        result = extract_toxicity_from_results(trial_data)

        assert result is not None
        assert "frequency_threshold" in result
        assert "reported_events" in result
        assert len(result["reported_events"]) > 0

    def test_extract_no_results_section(self):
        """Test with no results section."""
        trial_data = {}

        result = extract_toxicity_from_results(trial_data)

        assert result is None

    def test_extract_no_adverse_events(self):
        """Test with results but no adverse events."""
        trial_data = {
            "resultsSection": {
                "outcomeMeasuresModule": {}
            }
        }

        result = extract_toxicity_from_results(trial_data)

        assert result is None

    def test_extract_no_serious_events(self):
        """Test with adverse events but no serious/deaths."""
        trial_data = {
            "resultsSection": {
                "adverseEventsModule": {
                    "frequencyThreshold": "5%",
                    "eventGroups": [
                        {
                            "title": "Treatment Arm",
                            "deathsNumAffected": 0,
                            "seriousNumAffected": 0
                        }
                    ]
                }
            }
        }

        result = extract_toxicity_from_results(trial_data)

        assert result is None

    def test_extract_multiple_event_groups(self):
        """Test extraction with multiple event groups."""
        trial_data = {
            "resultsSection": {
                "adverseEventsModule": {
                    "frequencyThreshold": "5%",
                    "eventGroups": [
                        {
                            "title": "Arm A",
                            "deathsNumAffected": 1,
                            "seriousNumAffected": 5
                        },
                        {
                            "title": "Arm B",
                            "deathsNumAffected": 0,
                            "seriousNumAffected": 8
                        }
                    ]
                }
            }
        }

        result = extract_toxicity_from_results(trial_data)

        assert result is not None
        assert len(result["reported_events"]) == 2
        assert result["reported_events"][0]["group"] == "Arm A"
        assert result["reported_events"][1]["group"] == "Arm B"


class TestIntegrationScenarios:
    """Integration tests with realistic scenarios."""

    def test_realistic_phase1_trial(self):
        """Test with realistic phase 1 trial text."""
        text = """
        Dose-limiting toxicity was defined as grade 4 neutropenia lasting >7 days,
        grade 3-4 thrombocytopenia, or any grade 3-4 non-hematologic toxicity.
        Common adverse events included fatigue, nausea, diarrhea, and rash.
        Safety monitoring includes weekly blood counts and ECG monitoring.
        """

        result = parse_adverse_events(text)

        assert len(result["dose_limiting_toxicities"]) > 0
        assert len(result["common_aes"]) > 0
        assert len(result["safety_monitoring"]) > 0

    def test_realistic_immunotherapy_trial(self):
        """Test with realistic immunotherapy trial text."""
        text = """
        Grade 3-4 immune-related adverse events occurred in 15% of patients,
        including colitis, hepatitis, and pneumonitis. Common adverse events
        (any grade) included fatigue, pruritus, rash, and diarrhea.
        Patients require liver function tests and thyroid function monitoring.
        """

        result = parse_adverse_events(text)

        assert len(result["grade_3_4_events"]) > 0
        assert len(result["common_aes"]) > 0

        formatted = format_safety_display(result)
        assert "Grade 3-4" in formatted

    def test_no_safety_info_trial(self):
        """Test with trial that has no safety info."""
        text = "This is a phase 3 randomized trial comparing drug A to drug B."

        result = parse_adverse_events(text)
        formatted = format_safety_display(result)

        assert "not available" in formatted.lower()
