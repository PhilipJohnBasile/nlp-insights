"""Tests for clinical data extraction functions."""

import json
import pytest
import pandas as pd
from pathlib import Path
from trials.clinical_data import (
    extract_interventions,
    extract_locations,
    extract_sponsor_info,
    extract_outcomes,
    extract_conditions,
    extract_phase,
    extract_arms_info,
    create_clinical_dataframes
)


@pytest.fixture
def sample_trial_data():
    """Sample trial data for testing."""
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT12345678"
            },
            "armsInterventionsModule": {
                "interventions": [
                    {
                        "type": "DRUG",
                        "name": "Pembrolizumab",
                        "description": "200mg IV every 3 weeks"
                    },
                    {
                        "type": "DRUG",
                        "name": "Carboplatin",
                        "description": "AUC 5 IV every 3 weeks"
                    },
                    {
                        "type": "PROCEDURE",
                        "name": "Biopsy",
                        "description": "Tumor biopsy at baseline"
                    }
                ],
                "armGroups": [
                    {
                        "label": "Treatment Arm",
                        "type": "EXPERIMENTAL",
                        "description": "Pembrolizumab + Carboplatin"
                    },
                    {
                        "label": "Control Arm",
                        "type": "PLACEBO_COMPARATOR",
                        "description": "Placebo"
                    }
                ]
            },
            "contactsLocationsModule": {
                "locations": [
                    {
                        "facility": "Memorial Hospital",
                        "city": "Boston",
                        "state": "Massachusetts",
                        "zip": "02115",
                        "country": "United States",
                        "status": "Recruiting",
                        "geoPoint": {
                            "lat": 42.3601,
                            "lon": -71.0589
                        },
                        "contacts": [
                            {
                                "name": "John Doe, MD",
                                "phone": "555-1234",
                                "email": "jdoe@hospital.org"
                            }
                        ]
                    }
                ]
            },
            "sponsorCollaboratorsModule": {
                "leadSponsor": {
                    "name": "Pharma Corp",
                    "class": "INDUSTRY"
                }
            },
            "outcomesModule": {
                "primaryOutcomes": [
                    {"measure": "Overall Survival"},
                    {"measure": "Progression Free Survival"}
                ],
                "secondaryOutcomes": [
                    {"measure": "Response Rate"},
                    {"measure": "Safety and Tolerability"}
                ]
            },
            "conditionsModule": {
                "conditions": ["Lung Cancer", "Non-Small Cell Lung Cancer"]
            },
            "designModule": {
                "phases": ["PHASE2", "PHASE3"]
            }
        }
    }


class TestExtractInterventions:
    """Test intervention extraction."""

    def test_extract_drugs(self, sample_trial_data):
        """Test extracting drug interventions."""
        interventions, summary = extract_interventions(sample_trial_data)

        assert len(interventions) == 3
        assert summary["num_drugs"] == 2
        assert summary["is_combination"] is True
        assert "Pembrolizumab" in summary["drug_names"]
        assert "Carboplatin" in summary["drug_names"]

    def test_intervention_details(self, sample_trial_data):
        """Test intervention details."""
        interventions, _ = extract_interventions(sample_trial_data)

        drug = interventions[0]
        assert drug["type"] == "DRUG"
        assert drug["name"] == "Pembrolizumab"
        assert "200mg" in drug["description"]

    def test_empty_interventions(self):
        """Test with no interventions."""
        trial_data = {"protocolSection": {}}
        interventions, summary = extract_interventions(trial_data)

        assert interventions == []
        assert summary["num_drugs"] == 0
        assert summary["is_combination"] is False

    def test_single_drug(self, sample_trial_data):
        """Test single drug (not combination)."""
        sample_trial_data["protocolSection"]["armsInterventionsModule"]["interventions"] = [
            {
                "type": "DRUG",
                "name": "Pembrolizumab",
                "description": "200mg IV"
            }
        ]

        _, summary = extract_interventions(sample_trial_data)
        assert summary["num_drugs"] == 1
        assert summary["is_combination"] is False

    def test_procedure_only(self):
        """Test procedure-only intervention."""
        trial_data = {
            "protocolSection": {
                "armsInterventionsModule": {
                    "interventions": [
                        {
                            "type": "PROCEDURE",
                            "name": "Surgery",
                            "description": "Surgical resection"
                        }
                    ]
                }
            }
        }

        interventions, summary = extract_interventions(trial_data)
        assert len(interventions) == 1
        assert summary["num_drugs"] == 0


class TestExtractLocations:
    """Test location extraction."""

    def test_extract_location_basic(self, sample_trial_data):
        """Test basic location extraction."""
        locations = extract_locations(sample_trial_data)

        assert len(locations) == 1
        loc = locations[0]
        assert loc["facility"] == "Memorial Hospital"
        assert loc["city"] == "Boston"
        assert loc["state"] == "Massachusetts"
        assert loc["country"] == "United States"

    def test_location_geo_coordinates(self, sample_trial_data):
        """Test geo coordinates extraction."""
        locations = extract_locations(sample_trial_data)

        loc = locations[0]
        assert loc["latitude"] == 42.3601
        assert loc["longitude"] == -71.0589

    def test_location_contact_info(self, sample_trial_data):
        """Test contact information extraction."""
        locations = extract_locations(sample_trial_data)

        loc = locations[0]
        assert loc["contact_name"] == "John Doe, MD"
        assert loc["contact_phone"] == "555-1234"
        assert loc["contact_email"] == "jdoe@hospital.org"

    def test_location_no_contacts(self):
        """Test location without contacts."""
        trial_data = {
            "protocolSection": {
                "contactsLocationsModule": {
                    "locations": [
                        {
                            "facility": "Test Hospital",
                            "city": "New York",
                            "geoPoint": {}
                        }
                    ]
                }
            }
        }

        locations = extract_locations(trial_data)
        assert locations[0]["contact_name"] is None
        assert locations[0]["contact_phone"] is None

    def test_empty_locations(self):
        """Test with no locations."""
        trial_data = {"protocolSection": {}}
        locations = extract_locations(trial_data)
        assert locations == []

    def test_multiple_locations(self):
        """Test multiple locations."""
        trial_data = {
            "protocolSection": {
                "contactsLocationsModule": {
                    "locations": [
                        {"facility": "Hospital A", "city": "Boston"},
                        {"facility": "Hospital B", "city": "New York"},
                        {"facility": "Hospital C", "city": "Chicago"}
                    ]
                }
            }
        }

        locations = extract_locations(trial_data)
        assert len(locations) == 3


class TestExtractSponsorInfo:
    """Test sponsor information extraction."""

    def test_basic_sponsor_info(self, sample_trial_data):
        """Test basic sponsor extraction."""
        sponsor_info = extract_sponsor_info(sample_trial_data)

        assert sponsor_info["sponsor_name"] == "Pharma Corp"
        assert sponsor_info["sponsor_class"] == "INDUSTRY"

    def test_empty_sponsor_info(self):
        """Test with no sponsor."""
        trial_data = {"protocolSection": {}}
        sponsor_info = extract_sponsor_info(trial_data)

        assert sponsor_info["sponsor_name"] == ""
        assert sponsor_info["sponsor_class"] == ""

    def test_nih_sponsor(self):
        """Test NIH sponsor."""
        trial_data = {
            "protocolSection": {
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {
                        "name": "National Cancer Institute",
                        "class": "NIH"
                    }
                }
            }
        }

        sponsor_info = extract_sponsor_info(trial_data)
        assert sponsor_info["sponsor_class"] == "NIH"


class TestExtractOutcomes:
    """Test outcomes extraction."""

    def test_primary_outcomes(self, sample_trial_data):
        """Test primary outcomes extraction."""
        outcomes = extract_outcomes(sample_trial_data)

        assert len(outcomes["primary_outcomes"]) == 2
        assert "Overall Survival" in outcomes["primary_outcomes"]
        assert "Progression Free Survival" in outcomes["primary_outcomes"]

    def test_secondary_outcomes(self, sample_trial_data):
        """Test secondary outcomes extraction."""
        outcomes = extract_outcomes(sample_trial_data)

        assert len(outcomes["secondary_outcomes"]) == 2
        assert "Response Rate" in outcomes["secondary_outcomes"]

    def test_empty_outcomes(self):
        """Test with no outcomes."""
        trial_data = {"protocolSection": {}}
        outcomes = extract_outcomes(trial_data)

        assert outcomes["primary_outcomes"] == []
        assert outcomes["secondary_outcomes"] == []

    def test_primary_only(self):
        """Test with only primary outcomes."""
        trial_data = {
            "protocolSection": {
                "outcomesModule": {
                    "primaryOutcomes": [{"measure": "Overall Survival"}]
                }
            }
        }

        outcomes = extract_outcomes(trial_data)
        assert len(outcomes["primary_outcomes"]) == 1
        assert outcomes["secondary_outcomes"] == []


class TestExtractConditions:
    """Test conditions extraction."""

    def test_basic_conditions(self, sample_trial_data):
        """Test basic conditions extraction."""
        conditions = extract_conditions(sample_trial_data)

        assert len(conditions) == 2
        assert "Lung Cancer" in conditions
        assert "Non-Small Cell Lung Cancer" in conditions

    def test_empty_conditions(self):
        """Test with no conditions."""
        trial_data = {"protocolSection": {}}
        conditions = extract_conditions(trial_data)
        assert conditions == []

    def test_single_condition(self):
        """Test single condition."""
        trial_data = {
            "protocolSection": {
                "conditionsModule": {
                    "conditions": ["Breast Cancer"]
                }
            }
        }

        conditions = extract_conditions(trial_data)
        assert len(conditions) == 1
        assert conditions[0] == "Breast Cancer"


class TestExtractPhase:
    """Test phase extraction."""

    def test_multiple_phases(self, sample_trial_data):
        """Test multiple phases."""
        phase = extract_phase(sample_trial_data)
        assert phase == "Phase 2/Phase 3"

    def test_single_phase(self):
        """Test single phase."""
        trial_data = {
            "protocolSection": {
                "designModule": {
                    "phases": ["PHASE2"]
                }
            }
        }

        phase = extract_phase(trial_data)
        assert phase == "Phase 2"

    def test_no_phase(self):
        """Test with no phase."""
        trial_data = {"protocolSection": {"designModule": {}}}
        phase = extract_phase(trial_data)
        assert phase == "Not Applicable"

    def test_phase_na(self):
        """Test with NA phase."""
        trial_data = {
            "protocolSection": {
                "designModule": {
                    "phases": ["NA"]
                }
            }
        }

        phase = extract_phase(trial_data)
        assert "Not Applicable" in phase

    def test_phase_formatting(self):
        """Test phase formatting."""
        trial_data = {
            "protocolSection": {
                "designModule": {
                    "phases": ["PHASE1", "PHASE2"]
                }
            }
        }

        phase = extract_phase(trial_data)
        assert "Phase 1" in phase
        assert "Phase 2" in phase


class TestExtractArmsInfo:
    """Test arms information extraction."""

    def test_basic_arms_info(self, sample_trial_data):
        """Test basic arms extraction."""
        arms_info = extract_arms_info(sample_trial_data)

        assert arms_info["num_arms"] == 2
        assert arms_info["has_placebo"] is True
        assert arms_info["has_active_control"] is False
        assert arms_info["study_design"] == "Placebo-Controlled"

    def test_arms_list(self, sample_trial_data):
        """Test arms list extraction."""
        arms_info = extract_arms_info(sample_trial_data)

        arms = arms_info["arms"]
        assert len(arms) == 2
        assert arms[0]["label"] == "Treatment Arm"
        assert arms[0]["type"] == "EXPERIMENTAL"

    def test_single_arm(self):
        """Test single arm study."""
        trial_data = {
            "protocolSection": {
                "armsInterventionsModule": {
                    "armGroups": [
                        {
                            "label": "Treatment",
                            "type": "EXPERIMENTAL",
                            "description": "Drug A"
                        }
                    ]
                }
            }
        }

        arms_info = extract_arms_info(trial_data)
        assert arms_info["num_arms"] == 1
        assert arms_info["study_design"] == "Single Arm"

    def test_active_control(self):
        """Test active control study."""
        trial_data = {
            "protocolSection": {
                "armsInterventionsModule": {
                    "armGroups": [
                        {
                            "label": "Experimental",
                            "type": "EXPERIMENTAL",
                            "description": "Drug A"
                        },
                        {
                            "label": "Control",
                            "type": "ACTIVE_COMPARATOR",
                            "description": "Drug B"
                        }
                    ]
                }
            }
        }

        arms_info = extract_arms_info(trial_data)
        assert arms_info["has_active_control"] is True
        assert arms_info["has_placebo"] is False
        assert arms_info["study_design"] == "Active-Controlled"

    def test_multiple_arms_no_control(self):
        """Test multiple arms without control."""
        trial_data = {
            "protocolSection": {
                "armsInterventionsModule": {
                    "armGroups": [
                        {"label": "Arm 1", "type": "EXPERIMENTAL", "description": "Dose 1"},
                        {"label": "Arm 2", "type": "EXPERIMENTAL", "description": "Dose 2"},
                        {"label": "Arm 3", "type": "EXPERIMENTAL", "description": "Dose 3"}
                    ]
                }
            }
        }

        arms_info = extract_arms_info(trial_data)
        assert arms_info["num_arms"] == 3
        assert arms_info["study_design"] == "3 Arms"

    def test_empty_arms(self):
        """Test with no arms."""
        trial_data = {"protocolSection": {}}
        arms_info = extract_arms_info(trial_data)

        assert arms_info["num_arms"] == 0
        # With 0 arms, study design is "0 Arms" not "Single Arm"
        assert arms_info["study_design"] == "0 Arms"


class TestCreateClinicalDataframes:
    """Test creating clinical dataframes from JSONL file."""

    def test_create_dataframes(self, tmp_path, sample_trial_data):
        """Test creating dataframes from JSONL."""
        # Create temporary JSONL file
        jsonl_file = tmp_path / "trials.jsonl"
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(sample_trial_data) + '\n')

        # Process
        interventions_df, locations_df, clinical_df = create_clinical_dataframes(jsonl_file)

        # Verify interventions
        assert len(interventions_df) == 3
        assert "trial_id" in interventions_df.columns
        assert interventions_df["trial_id"].iloc[0] == "NCT12345678"

        # Verify locations
        assert len(locations_df) == 1
        assert locations_df["facility"].iloc[0] == "Memorial Hospital"

        # Verify clinical details
        assert len(clinical_df) == 1
        assert clinical_df["trial_id"].iloc[0] == "NCT12345678"
        assert clinical_df["sponsor_name"].iloc[0] == "Pharma Corp"
        assert clinical_df["num_drugs"].iloc[0] == 2
        # Use == True instead of 'is True' for numpy boolean
        assert clinical_df["is_combination"].iloc[0] == True

    def test_multiple_trials(self, tmp_path, sample_trial_data):
        """Test processing multiple trials."""
        # Create second trial
        trial_data_2 = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT99999999"},
                "armsInterventionsModule": {
                    "interventions": [{"type": "DRUG", "name": "Drug X", "description": "Test"}],
                    "armGroups": [{"label": "Arm 1", "type": "EXPERIMENTAL", "description": "Test"}]
                },
                "contactsLocationsModule": {"locations": []},
                "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Test Corp", "class": "INDUSTRY"}},
                "outcomesModule": {},
                "conditionsModule": {"conditions": ["Test Condition"]},
                "designModule": {"phases": ["PHASE1"]}
            }
        }

        # Create JSONL file
        jsonl_file = tmp_path / "trials.jsonl"
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(sample_trial_data) + '\n')
            f.write(json.dumps(trial_data_2) + '\n')

        # Process
        interventions_df, locations_df, clinical_df = create_clinical_dataframes(jsonl_file)

        # Verify
        assert len(clinical_df) == 2
        assert "NCT12345678" in clinical_df["trial_id"].values
        assert "NCT99999999" in clinical_df["trial_id"].values

    def test_missing_nct_id(self, tmp_path):
        """Test skipping trials without NCT ID."""
        trial_data = {"protocolSection": {}}

        jsonl_file = tmp_path / "trials.jsonl"
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(trial_data) + '\n')

        interventions_df, locations_df, clinical_df = create_clinical_dataframes(jsonl_file)

        # Should skip trial
        assert len(clinical_df) == 0
