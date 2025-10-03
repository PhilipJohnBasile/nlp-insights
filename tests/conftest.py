"""Pytest configuration and shared fixtures for all tests."""

import pytest
import pandas as pd
from pathlib import Path
from typing import Dict, List
import tempfile
import shutil


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_trial_json():
    """Sample clinical trial JSON data."""
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT12345678",
                "briefTitle": "Test Phase 2 Trial in NSCLC",
                "officialTitle": "A Phase 2 Study of Novel Agent in Advanced NSCLC"
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "startDateStruct": {"date": "2024-01-01"},
                "completionDateStruct": {"date": "2025-12-31"},
                "lastUpdatePostDateStruct": {"date": "2024-03-01"}
            },
            "sponsorCollaboratorsModule": {
                "leadSponsor": {
                    "name": "Test Pharmaceutical Company"
                },
                "collaborators": []
            },
            "descriptionModule": {
                "briefSummary": "This is a phase 2 trial testing a novel agent in patients with advanced NSCLC.",
                "detailedDescription": "Detailed description of the trial methodology and objectives."
            },
            "designModule": {
                "phases": ["PHASE2"],
                "studyType": "INTERVENTIONAL",
                "designInfo": {
                    "allocation": "RANDOMIZED",
                    "maskingInfo": {"masking": "DOUBLE"}
                }
            },
            "armsInterventionsModule": {
                "interventions": [
                    {
                        "type": "DRUG",
                        "name": "Novel Agent X",
                        "description": "Experimental drug"
                    }
                ]
            },
            "eligibilityModule": {
                "eligibilityCriteria": """
                Inclusion Criteria:
                - Age ≥18 years
                - Histologically confirmed NSCLC
                - EGFR exon 19 deletion or L858R mutation
                - PD-L1 expression ≥50%
                - ECOG performance status 0-1
                - Treatment-naive advanced disease
                - Adequate organ function

                Exclusion Criteria:
                - Untreated brain metastases
                - Prior EGFR TKI therapy
                - Active autoimmune disease
                - HIV, HBV, or HCV infection
                - Pregnant or nursing women
                """,
                "sex": "ALL",
                "minimumAge": "18 Years",
                "maximumAge": "N/A",
                "healthyVolunteers": False
            },
            "contactsLocationsModule": {
                "locations": [
                    {
                        "facility": "Memorial Cancer Center",
                        "city": "Boston",
                        "state": "Massachusetts",
                        "zip": "02115",
                        "country": "United States",
                        "status": "RECRUITING",
                        "geoPoint": {
                            "lat": 42.3601,
                            "lon": -71.0589
                        }
                    },
                    {
                        "facility": "University Medical Center",
                        "city": "Los Angeles",
                        "state": "California",
                        "zip": "90033",
                        "country": "United States",
                        "status": "RECRUITING",
                        "geoPoint": {
                            "lat": 34.0522,
                            "lon": -118.2437
                        }
                    }
                ],
                "centralContacts": [
                    {
                        "name": "Study Coordinator",
                        "phone": "555-1234",
                        "email": "coordinator@example.com"
                    }
                ]
            },
            "outcomesModule": {
                "primaryOutcomes": [
                    {
                        "measure": "Objective Response Rate",
                        "description": "Proportion of patients achieving CR or PR",
                        "timeFrame": "24 months"
                    }
                ],
                "secondaryOutcomes": [
                    {
                        "measure": "Progression-Free Survival",
                        "timeFrame": "36 months"
                    },
                    {
                        "measure": "Overall Survival",
                        "timeFrame": "60 months"
                    }
                ]
            }
        }
    }


@pytest.fixture
def sample_trials_df():
    """Sample trials DataFrame."""
    return pd.DataFrame([
        {
            "trial_id": "NCT12345678",
            "title": "Phase 2 Study in EGFR+ NSCLC",
            "status": "RECRUITING",
            "phase": "Phase 2",
            "brief_summary": "Testing novel EGFR inhibitor",
            "start_date": "2024-01-01",
            "sponsor": "Test Pharma"
        },
        {
            "trial_id": "NCT87654321",
            "title": "Phase 3 Immunotherapy Trial",
            "status": "RECRUITING",
            "phase": "Phase 3",
            "brief_summary": "Comparing immunotherapy regimens",
            "start_date": "2024-02-01",
            "sponsor": "Academic Medical Center"
        },
        {
            "trial_id": "NCT11111111",
            "title": "Phase 1 Dose Escalation Study",
            "status": "ACTIVE_NOT_RECRUITING",
            "phase": "Phase 1",
            "brief_summary": "Finding optimal dose of new agent",
            "start_date": "2023-06-01",
            "sponsor": "Biotech Inc"
        }
    ])


@pytest.fixture
def sample_eligibility_df():
    """Sample eligibility DataFrame."""
    return pd.DataFrame([
        {
            "trial_id": "NCT12345678",
            "eligibility_text": """
            Inclusion Criteria:
            - EGFR mutation positive NSCLC
            - ECOG 0-1
            - Age >= 18 years

            Exclusion Criteria:
            - Brain metastases
            - Prior EGFR TKI
            """,
            "min_age": "18",
            "max_age": "N/A",
            "sex": "ALL"
        },
        {
            "trial_id": "NCT87654321",
            "eligibility_text": """
            Inclusion Criteria:
            - PD-L1 >= 50%
            - Treatment naive
            - ECOG 0-2

            Exclusion Criteria:
            - Prior immunotherapy
            - Autoimmune disease
            """,
            "min_age": "18",
            "max_age": "N/A",
            "sex": "ALL"
        }
    ])


@pytest.fixture
def sample_locations_df():
    """Sample locations DataFrame."""
    return pd.DataFrame([
        {
            "trial_id": "NCT12345678",
            "facility": "Memorial Cancer Center",
            "city": "Boston",
            "state": "Massachusetts",
            "country": "United States",
            "status": "RECRUITING",
            "latitude": 42.3601,
            "longitude": -71.0589
        },
        {
            "trial_id": "NCT12345678",
            "facility": "University Medical Center",
            "city": "Los Angeles",
            "state": "California",
            "country": "United States",
            "status": "RECRUITING",
            "latitude": 34.0522,
            "longitude": -118.2437
        },
        {
            "trial_id": "NCT87654321",
            "facility": "City Hospital",
            "city": "New York",
            "state": "New York",
            "country": "United States",
            "status": "RECRUITING",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
    ])


@pytest.fixture
def sample_clinical_details_df():
    """Sample clinical details DataFrame."""
    return pd.DataFrame([
        {
            "trial_id": "NCT12345678",
            "phase": "Phase 2",
            "study_type": "INTERVENTIONAL",
            "allocation": "RANDOMIZED",
            "masking": "DOUBLE",
            "sponsor_name": "Test Pharma",
            "primary_outcomes": ["Objective Response Rate"],
            "secondary_outcomes": ["Progression-Free Survival", "Overall Survival"]
        },
        {
            "trial_id": "NCT87654321",
            "phase": "Phase 3",
            "study_type": "INTERVENTIONAL",
            "allocation": "RANDOMIZED",
            "masking": "NONE",
            "sponsor_name": "Academic Medical Center",
            "primary_outcomes": ["Overall Survival"],
            "secondary_outcomes": ["Quality of Life"]
        }
    ])


@pytest.fixture
def sample_patient_data():
    """Sample patient data for matching."""
    return {
        "age": 65,
        "sex": "Male",
        "cancer_type": "lung cancer",
        "cancer_stage": "IV",
        "ecog_status": "1",
        "prior_therapies": 0,
        "biomarkers": {
            "egfr": True,
            "alk": False,
            "ros1": False,
            "pdl1": True,
            "her2": False
        },
        "conditions": {
            "brain_mets": False,
            "autoimmune": False,
            "hiv": False,
            "hepatitis": False
        },
        "location": {
            "state": "Massachusetts",
            "city": "Boston"
        }
    }


@pytest.fixture
def sample_eligibility_texts():
    """Sample eligibility criteria texts for parsing tests."""
    return {
        "nsclc_egfr": """
        Inclusion Criteria:
        - Histologically confirmed NSCLC
        - EGFR exon 19 deletion or L858R mutation
        - Treatment-naive advanced disease
        - ECOG performance status 0-1
        - PD-L1 expression ≥50%

        Exclusion Criteria:
        - Untreated brain metastases
        - Prior EGFR TKI therapy
        - Active autoimmune disease
        """,
        "immunotherapy": """
        Inclusion Criteria:
        - MSI-High or dMMR solid tumors
        - Disease progression after 1-2 prior therapies
        - ECOG PS 0-2
        - No more than 3 prior lines of therapy
        - 4 weeks washout from prior therapy

        Exclusion Criteria:
        - Prior immune checkpoint inhibitor
        - HIV, HBV, or HCV positive
        - Organ dysfunction
        """,
        "glioblastoma": """
        Inclusion Criteria:
        - IDH-mutant glioblastoma
        - MGMT methylated
        - First-line therapy
        - KPS ≥70
        - Brain MRI and genomic profiling required

        Exclusion Criteria:
        - Prior radiation to brain
        - Pregnancy
        """
    }


@pytest.fixture
def mock_api_response():
    """Mock API response from ClinicalTrials.gov."""
    return {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT99999999"
                    }
                }
            }
        ],
        "totalCount": 1
    }


# Pytest configuration
def pytest_configure(config):
    """Pytest configuration hook."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# Custom assertions
def assert_valid_nct_id(nct_id: str):
    """Assert that NCT ID has valid format."""
    assert nct_id.startswith("NCT"), f"NCT ID {nct_id} doesn't start with 'NCT'"
    assert len(nct_id) == 11, f"NCT ID {nct_id} is not 11 characters"
    assert nct_id[3:].isdigit(), f"NCT ID {nct_id} doesn't have 8 digits after 'NCT'"


def assert_dataframe_has_columns(df: pd.DataFrame, required_columns: List[str]):
    """Assert DataFrame has all required columns."""
    missing = set(required_columns) - set(df.columns)
    assert not missing, f"DataFrame missing required columns: {missing}"


# Pytest plugins
pytest_plugins = []
