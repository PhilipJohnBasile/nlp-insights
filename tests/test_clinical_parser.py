"""Unit tests for clinical trial data parsing."""

import pytest
from trials.clinical_parser import (
    split_inclusion_exclusion,
    parse_treatment_line,
    check_common_exclusions,
    parse_biomarker_requirements,
    parse_prior_lines_limit,
    parse_washout_period,
    parse_required_tests,
    parse_ecog_requirement,
    parse_dose_escalation_info,
    parse_randomization_info,
    parse_crossover_info,
    extract_contact_from_location
)


class TestSplitInclusionExclusion:
    """Test cases for splitting inclusion/exclusion criteria."""

    def test_clear_sections(self):
        """Test with clearly marked sections."""
        text = """
        Inclusion Criteria:
        - Age >= 18 years
        - Confirmed diagnosis

        Exclusion Criteria:
        - Pregnant women
        - Active infection
        """

        inclusion, exclusion = split_inclusion_exclusion(text)

        assert "Age >= 18" in inclusion
        assert "Confirmed diagnosis" in inclusion
        assert "Pregnant" in exclusion
        assert "Active infection" in exclusion

    def test_case_insensitive(self):
        """Test case-insensitive section detection."""
        text = """
        INCLUSION CRITERIA:
        - Patient requirement

        EXCLUSION CRITERIA:
        - Exclusion item
        """

        inclusion, exclusion = split_inclusion_exclusion(text)

        assert "Patient requirement" in inclusion
        assert "Exclusion item" in exclusion

    def test_no_clear_sections(self):
        """Test with no clear section markers."""
        text = "Age >= 18 years and confirmed diagnosis required"

        inclusion, exclusion = split_inclusion_exclusion(text)

        # Should assume all is inclusion
        assert text in inclusion
        assert exclusion == ""

    def test_empty_input(self):
        """Test with empty input."""
        inclusion, exclusion = split_inclusion_exclusion(None)

        assert inclusion == ""
        assert exclusion == ""

    def test_only_inclusion(self):
        """Test with only inclusion criteria."""
        text = """
        Inclusion Criteria:
        - Age >= 18
        - Performance status 0-1
        """

        inclusion, exclusion = split_inclusion_exclusion(text)

        assert "Age >= 18" in inclusion
        assert exclusion == "" or len(exclusion) < 10


class TestParseTreatmentLine:
    """Test cases for treatment line parsing."""

    def test_first_line(self):
        """Test detection of first-line trials."""
        text = "Treatment-naive patients with previously untreated disease"
        result = parse_treatment_line(text)

        assert result["treatment_line"] == "1st line"
        assert result["treatment_naive_allowed"] is True
        assert result["prior_therapy_required"] is False

    def test_second_line(self):
        """Test detection of second-line trials."""
        text = "Patients with disease progression after one prior line of therapy"
        result = parse_treatment_line(text)

        assert result["treatment_line"] == "2nd line"
        assert result["prior_therapy_required"] is True
        assert result["treatment_naive_allowed"] is False

    def test_third_line_plus(self):
        """Test detection of heavily pretreated patients."""
        text = "Patients with relapsed or refractory disease after two or more prior therapies"
        result = parse_treatment_line(text)

        assert result["treatment_line"] == "3rd+ line"
        assert result["prior_therapy_required"] is True

    def test_any_line(self):
        """Test when line is not specified."""
        text = "Patients with advanced cancer"
        result = parse_treatment_line(text)

        assert result["treatment_line"] == "Any line"

    def test_empty_input(self):
        """Test with empty input."""
        result = parse_treatment_line(None)

        assert result["treatment_line"] == "Unknown"


class TestCheckCommonExclusions:
    """Test cases for common exclusions checking."""

    def test_brain_mets_excluded(self):
        """Test detection of brain metastases exclusion."""
        text = """
        Exclusion Criteria:
        - Untreated brain metastases
        - Active CNS disease
        """

        result = check_common_exclusions(text)

        assert result["brain_mets_excluded"] is True

    def test_brain_mets_allowed(self):
        """Test detection when brain metastases are allowed."""
        text = "Stable brain metastases allowed if previously treated"

        result = check_common_exclusions(text)

        assert result["brain_mets_excluded"] is False

    def test_prior_immunotherapy_excluded(self):
        """Test detection of prior immunotherapy exclusion."""
        text = "Exclusion Criteria: Prior treatment with PD-1 or PD-L1 inhibitors"

        result = check_common_exclusions(text)

        assert result["prior_immunotherapy_excluded"] is True

    def test_autoimmune_excluded(self):
        """Test detection of autoimmune disease exclusion."""
        text = "Exclusion Criteria: Active autoimmune disease requiring systemic therapy"

        result = check_common_exclusions(text)

        assert result["autoimmune_excluded"] is True

    def test_hiv_excluded(self):
        """Test detection of HIV exclusion."""
        text = "Exclusion: Known HIV positive status"

        result = check_common_exclusions(text)

        assert result["hiv_excluded"] is True

    def test_hepatitis_excluded(self):
        """Test detection of hepatitis exclusion."""
        text = "Exclusion: Active hepatitis B or C infection"

        result = check_common_exclusions(text)

        assert result["hepatitis_excluded"] is True

    def test_multiple_exclusions(self):
        """Test detection of multiple exclusions."""
        text = """
        Exclusion Criteria:
        - Brain metastases
        - Prior immunotherapy
        - Autoimmune disease
        - HIV or HCV positive
        """

        result = check_common_exclusions(text)

        assert result["brain_mets_excluded"] is True
        assert result["prior_immunotherapy_excluded"] is True
        assert result["autoimmune_excluded"] is True
        assert result["hiv_excluded"] is True
        assert result["hepatitis_excluded"] is True

    def test_empty_input(self):
        """Test with empty input."""
        result = check_common_exclusions(None)

        assert result == {}


class TestParseBiomarkerRequirements:
    """Test cases for biomarker requirement parsing."""

    def test_pdl1_cutoff(self):
        """Test PD-L1 expression cutoff detection."""
        text = "PD-L1 expression ≥50% required"
        result = parse_biomarker_requirements(text)

        assert "pdl1_cutoff" in result
        assert "50" in result["pdl1_cutoff"]

    def test_her2_positive(self):
        """Test HER2-positive requirement."""
        text = "HER2+ breast cancer required"
        result = parse_biomarker_requirements(text)

        assert result.get("her2_status") == "Positive"

    def test_egfr_mutation(self):
        """Test EGFR mutation detection."""
        text = "EGFR-mutant non-small cell lung cancer with exon 19 deletion or L858R"
        result = parse_biomarker_requirements(text)

        assert result.get("egfr_mutation") is True
        # Should detect specific mutation
        assert "egfr_specific" in result

    def test_alk_rearrangement(self):
        """Test ALK rearrangement detection."""
        text = "ALK-positive NSCLC with ALK fusion confirmed"
        result = parse_biomarker_requirements(text)

        assert result.get("alk_rearrangement") is True

    def test_brca_mutation(self):
        """Test BRCA mutation detection."""
        text = "BRCA1 or BRCA2 mutation carriers"
        result = parse_biomarker_requirements(text)

        assert result.get("brca_mutation") is True

    def test_msi_high(self):
        """Test MSI-high detection."""
        text = "Microsatellite instability-high (MSI-H) tumors"
        result = parse_biomarker_requirements(text)

        assert result.get("msi_status") == "MSI-High"

    def test_mmr_deficient(self):
        """Test MMR deficiency detection."""
        text = "Mismatch repair deficient (dMMR) tumors"
        result = parse_biomarker_requirements(text)

        assert result.get("mmr_status") == "Deficient"

    def test_idh_mutation(self):
        """Test IDH mutation detection (gliomas)."""
        text = "IDH1-mutant glioblastoma"
        result = parse_biomarker_requirements(text)

        assert result.get("idh_mutation") is True

    def test_mgmt_methylation(self):
        """Test MGMT methylation detection."""
        text = "MGMT methylated glioblastoma"
        result = parse_biomarker_requirements(text)

        assert result.get("mgmt_methylated") is True

    def test_multiple_biomarkers(self):
        """Test detection of multiple biomarkers."""
        text = """
        EGFR mutation positive NSCLC with PD-L1 ≥1%.
        HER2+ patients also eligible.
        """
        result = parse_biomarker_requirements(text)

        assert result.get("egfr_mutation") is True
        assert "pdl1" in str(result).lower()
        assert result.get("her2_status") == "Positive"

    def test_empty_input(self):
        """Test with empty input."""
        result = parse_biomarker_requirements(None)

        assert result == {}


class TestParsePriorLinesLimit:
    """Test cases for prior therapy lines limit parsing."""

    def test_no_more_than_pattern(self):
        """Test 'no more than X prior' pattern."""
        text = "No more than 3 prior lines of therapy"
        result = parse_prior_lines_limit(text)

        assert result == 3

    def test_maximum_pattern(self):
        """Test 'maximum X prior' pattern."""
        text = "Maximum 2 prior systemic therapies"
        result = parse_prior_lines_limit(text)

        assert result == 2

    def test_up_to_pattern(self):
        """Test 'up to X prior' pattern."""
        text = "Up to 4 prior therapies allowed"
        result = parse_prior_lines_limit(text)

        assert result == 4

    def test_exclusion_pattern(self):
        """Test exclusion pattern '>X prior'."""
        text = """
        Exclusion Criteria:
        - More than 5 prior lines of therapy
        """
        result = parse_prior_lines_limit(text)

        assert result == 5

    def test_no_limit(self):
        """Test when no limit is specified."""
        text = "Patients with relapsed disease"
        result = parse_prior_lines_limit(text)

        assert result is None

    def test_empty_input(self):
        """Test with empty input."""
        result = parse_prior_lines_limit(None)

        assert result is None


class TestParseWashoutPeriod:
    """Test cases for washout period parsing."""

    def test_weeks_pattern(self):
        """Test washout period in weeks."""
        text = "At least 4 weeks since last prior therapy"
        result = parse_washout_period(text)

        assert result == "4 weeks"

    def test_days_pattern(self):
        """Test washout period in days."""
        text = "14 days washout from prior chemotherapy"
        result = parse_washout_period(text)

        assert result == "14 days"

    def test_washout_keyword(self):
        """Test with 'washout' keyword."""
        text = "Washout period of 3 weeks required"
        result = parse_washout_period(text)

        assert result == "3 weeks"

    def test_no_washout(self):
        """Test when no washout is mentioned."""
        text = "Patients with advanced cancer"
        result = parse_washout_period(text)

        assert result is None

    def test_empty_input(self):
        """Test with empty input."""
        result = parse_washout_period(None)

        assert result is None


class TestParseRequiredTests:
    """Test cases for required tests parsing."""

    def test_tissue_biopsy(self):
        """Test tissue biopsy requirement."""
        text = "Fresh tumor biopsy required for eligibility"
        result = parse_required_tests(text)

        assert any("biopsy" in test.lower() for test in result)

    def test_pet_scan(self):
        """Test PET scan requirement."""
        text = "Baseline PET-CT scan required"
        result = parse_required_tests(text)

        assert any("pet" in test.lower() for test in result)

    def test_brain_mri(self):
        """Test brain MRI requirement."""
        text = "Brain MRI within 4 weeks of enrollment"
        result = parse_required_tests(text)

        assert any("mri" in test.lower() for test in result)

    def test_cardiac_function(self):
        """Test cardiac function test requirement."""
        text = "LVEF assessment via echocardiogram or MUGA"
        result = parse_required_tests(text)

        assert any("cardiac" in test.lower() or "echo" in test.lower() for test in result)

    def test_genomic_profiling(self):
        """Test genomic profiling requirement."""
        text = "Next-generation sequencing (NGS) required"
        result = parse_required_tests(text)

        assert any("genomic" in test.lower() or "ngs" in test.lower() for test in result)

    def test_multiple_tests(self):
        """Test detection of multiple required tests."""
        text = """
        Required baseline assessments:
        - Fresh tumor biopsy
        - PET-CT scan
        - Brain MRI
        - Echocardiogram for LVEF
        - NGS genomic profiling
        """
        result = parse_required_tests(text)

        # Should detect multiple tests
        assert len(result) >= 3

    def test_empty_input(self):
        """Test with empty input."""
        result = parse_required_tests(None)

        assert result == []


class TestParseEcogRequirement:
    """Test cases for ECOG requirement parsing."""

    def test_ecog_0_1(self):
        """Test ECOG 0-1 requirement."""
        text = "ECOG performance status 0-1"
        result = parse_ecog_requirement(text)

        assert result["max_ecog"] == 1

    def test_ecog_0_2(self):
        """Test ECOG 0-2 requirement."""
        text = "ECOG PS ≤2"
        result = parse_ecog_requirement(text)

        assert result["max_ecog"] == 2

    def test_ecog_symbol(self):
        """Test ECOG with ≤ symbol."""
        text = "ECOG performance status ≤ 1"
        result = parse_ecog_requirement(text)

        assert result["max_ecog"] == 1

    def test_ecog_or_pattern(self):
        """Test ECOG 'or' pattern."""
        text = "ECOG 0 or 1"
        result = parse_ecog_requirement(text)

        assert result["max_ecog"] == 1

    def test_no_ecog_requirement(self):
        """Test when ECOG is not mentioned."""
        text = "Patients with advanced cancer"
        result = parse_ecog_requirement(text)

        assert result["max_ecog"] is None

    def test_empty_input(self):
        """Test with empty input."""
        result = parse_ecog_requirement(None)

        assert result["max_ecog"] is None


class TestIntegrationScenarios:
    """Integration tests with realistic trial scenarios."""

    def test_realistic_nsclc_trial(self):
        """Test with realistic NSCLC trial eligibility."""
        text = """
        Inclusion Criteria:
        - Age ≥18 years
        - EGFR exon 19 deletion or L858R mutation
        - PD-L1 expression ≥50%
        - ECOG performance status 0-1
        - Treatment-naive advanced NSCLC
        - Fresh tumor biopsy required

        Exclusion Criteria:
        - Untreated brain metastases
        - Prior EGFR TKI therapy
        - Active autoimmune disease
        """

        inclusion, exclusion = split_inclusion_exclusion(text)
        biomarkers = parse_biomarker_requirements(text)
        treatment_line = parse_treatment_line(text)
        exclusions = check_common_exclusions(text)
        ecog = parse_ecog_requirement(text)
        tests = parse_required_tests(text)

        assert "Age" in inclusion
        assert biomarkers.get("egfr_mutation") is True
        assert "pdl1" in str(biomarkers).lower()
        assert treatment_line["treatment_line"] == "1st line"
        assert exclusions["brain_mets_excluded"] is True
        assert exclusions["autoimmune_excluded"] is True
        assert ecog["max_ecog"] == 1
        assert len(tests) > 0

    def test_realistic_immunotherapy_trial(self):
        """Test with realistic immunotherapy trial."""
        text = """
        Inclusion Criteria:
        - MSI-High or dMMR solid tumors
        - Disease progression after 1-2 prior therapies
        - ECOG PS 0-2
        - Archival tissue available
        - 4 weeks washout from prior therapy

        Exclusion Criteria:
        - Prior immune checkpoint inhibitor
        - HIV positive
        - Hepatitis B or C
        """

        biomarkers = parse_biomarker_requirements(text)
        treatment_line = parse_treatment_line(text)
        exclusions = check_common_exclusions(text)
        washout = parse_washout_period(text)
        prior_limit = parse_prior_lines_limit(text)

        assert biomarkers.get("msi_status") == "MSI-High" or biomarkers.get("mmr_status") == "Deficient"
        assert treatment_line["prior_therapy_required"] is True
        assert exclusions["prior_immunotherapy_excluded"] is True
        assert exclusions["hiv_excluded"] is True
        assert exclusions["hepatitis_excluded"] is True
        assert washout == "4 weeks"
        assert prior_limit == 2

    def test_realistic_glioblastoma_trial(self):
        """Test with realistic glioblastoma trial."""
        text = """
        Inclusion Criteria:
        - IDH-mutant glioblastoma
        - MGMT methylated
        - First-line therapy
        - KPS ≥70
        - Brain MRI and genomic profiling required
        """

        biomarkers = parse_biomarker_requirements(text)
        treatment_line = parse_treatment_line(text)
        tests = parse_required_tests(text)

        assert biomarkers.get("idh_mutation") is True
        assert biomarkers.get("mgmt_methylated") is True
        assert treatment_line["treatment_line"] == "1st line"
        assert any("mri" in test.lower() for test in tests)


class TestRequiredTests:
    """Test required tests parsing."""

    def test_archival_tissue(self):
        """Test archival tissue detection."""
        text = "Archival tissue required for molecular testing"
        tests = parse_required_tests(text)
        assert "Archival tissue" in tests

    def test_pet_scan(self):
        """Test PET scan detection."""
        text = "PET-CT scan required at baseline"
        tests = parse_required_tests(text)
        assert "PET scan" in tests

    def test_brain_mri(self):
        """Test brain MRI detection."""
        text = "Brain MRI required within 28 days"
        tests = parse_required_tests(text)
        assert "Brain MRI" in tests

    def test_cardiac_function(self):
        """Test cardiac function test detection."""
        text = "Echocardiogram or MUGA scan with LVEF >50%"
        tests = parse_required_tests(text)
        assert any("Cardiac" in test for test in tests)

    def test_bone_marrow_biopsy(self):
        """Test bone marrow biopsy detection."""
        text = "Bone marrow biopsy and aspiration required"
        tests = parse_required_tests(text)
        assert "Bone marrow biopsy" in tests

    def test_liquid_biopsy(self):
        """Test liquid biopsy detection."""
        text = "Liquid biopsy for ctDNA analysis"
        tests = parse_required_tests(text)
        assert any("Liquid biopsy" in test for test in tests)

    def test_genomic_profiling(self):
        """Test genomic profiling detection."""
        text = "Next-generation sequencing (NGS) required"
        tests = parse_required_tests(text)
        assert any("Genomic profiling" in test or "NGS" in test for test in tests)


class TestDoseEscalation:
    """Test dose escalation parsing."""

    def test_dose_escalation_detection(self):
        """Test dose escalation detection."""
        trial_data = {
            "protocolSection": {
                "identificationModule": {"briefTitle": "Phase 1a Dose Escalation Study"},
                "descriptionModule": {"briefSummary": "Dose finding study using 3+3 design"}
            }
        }
        result = parse_dose_escalation_info(trial_data)
        assert result["is_dose_escalation"] is True
        assert result["cohort_type"] == "Dose Escalation"

    def test_expansion_cohort_detection(self):
        """Test expansion cohort detection."""
        trial_data = {
            "protocolSection": {
                "identificationModule": {"briefTitle": "Phase 1b Expansion Study"},
                "descriptionModule": {"briefSummary": "Expansion cohort at RP2D"}
            }
        }
        result = parse_dose_escalation_info(trial_data)
        assert result["is_expansion"] is True

    def test_combined_escalation_expansion(self):
        """Test combined dose escalation and expansion."""
        trial_data = {
            "protocolSection": {
                "identificationModule": {"briefTitle": "Phase 1 Study"},
                "descriptionModule": {"briefSummary": "Dose escalation followed by expansion cohort"}
            }
        }
        result = parse_dose_escalation_info(trial_data)
        assert result["is_dose_escalation"] is True
        assert result["is_expansion"] is True
        assert "Expansion" in result["cohort_type"]

    def test_dose_level_extraction(self):
        """Test dose level extraction."""
        trial_data = {
            "protocolSection": {
                "identificationModule": {"briefTitle": "Phase 1a Dose Escalation Study"},
                "descriptionModule": {
                    "briefSummary": "Dose level 3 escalation",
                    "detailedDescription": "Patients will receive dose level 3 in the escalation phase"
                }
            }
        }
        result = parse_dose_escalation_info(trial_data)
        assert result["is_dose_escalation"] is True
        assert result["dose_level"] == "Level 3"

    def test_no_dose_escalation(self):
        """Test when no dose escalation."""
        trial_data = {
            "protocolSection": {
                "identificationModule": {"briefTitle": "Phase 3 Study"},
                "descriptionModule": {"briefSummary": "Randomized controlled trial"}
            }
        }
        result = parse_dose_escalation_info(trial_data)
        assert result["is_dose_escalation"] is False
        assert result["is_expansion"] is False


class TestRandomization:
    """Test randomization parsing."""

    def test_randomized_trial(self):
        """Test randomized trial detection."""
        trial_data = {
            "protocolSection": {
                "designModule": {
                    "designInfo": {
                        "allocation": "Randomized",
                        "interventionModel": "Parallel Assignment"
                    }
                }
            }
        }
        result = parse_randomization_info(trial_data)
        assert result["is_randomized"] is True
        assert result["allocation"] == "Randomized"

    def test_randomization_ratio_in_description(self):
        """Test randomization ratio extraction from description."""
        trial_data = {
            "protocolSection": {
                "designModule": {
                    "designInfo": {"allocation": "Randomized"}
                },
                "descriptionModule": {
                    "detailedDescription": "Patients will be randomized 2:1 to treatment vs placebo"
                }
            }
        }
        result = parse_randomization_info(trial_data)
        assert result["randomization_ratio"] == "2:1"

    def test_masking_detection(self):
        """Test masking detection."""
        trial_data = {
            "protocolSection": {
                "designModule": {
                    "designInfo": {
                        "allocation": "Randomized",
                        "maskingInfo": {"masking": "Double"}
                    }
                }
            }
        }
        result = parse_randomization_info(trial_data)
        assert result["masking"] == "Double"

    def test_non_randomized_trial(self):
        """Test non-randomized trial."""
        trial_data = {
            "protocolSection": {
                "designModule": {
                    "designInfo": {"allocation": "Non-Randomized"}
                }
            }
        }
        result = parse_randomization_info(trial_data)
        assert result["is_randomized"] is False


class TestCrossover:
    """Test crossover design parsing."""

    def test_crossover_allowed_detection(self):
        """Test crossover allowed detection in eligibility text."""
        text = "Patients may crossover to active treatment after progression"
        result = parse_crossover_info(text)
        assert result["crossover_allowed"] is True
        assert "Crossover to active treatment allowed" in result["crossover_details"]

    def test_crossover_not_allowed(self):
        """Test crossover not allowed detection."""
        text = "No crossover is permitted in this trial"
        result = parse_crossover_info(text)
        assert result["crossover_allowed"] is False

    def test_no_crossover_info(self):
        """Test when no crossover information."""
        result = parse_crossover_info("Standard eligibility criteria")
        assert result["crossover_allowed"] is None


class TestContactExtraction:
    """Test contact information extraction."""

    def test_extract_contact_with_full_info(self):
        """Test extracting contact with complete information."""
        location_data = {
            "facility": "University Hospital",
            "city": "Boston",
            "state": "MA",
            "zip": "02115",
            "country": "United States",
            "contacts": [
                {
                    "name": "Dr. John Smith",
                    "role": "Principal Investigator",
                    "phone": "617-555-1234",
                    "email": "john.smith@hospital.org"
                }
            ]
        }
        result = extract_contact_from_location(location_data)
        assert result["contact_name"] == "Dr. John Smith"
        assert result["contact_role"] == "Principal Investigator"
        assert result["contact_phone"] == "617-555-1234"
        assert result["contact_email"] == "john.smith@hospital.org"

    def test_extract_contact_no_contacts(self):
        """Test location with no contacts."""
        location_data = {
            "facility": "Hospital",
            "city": "Boston"
        }
        result = extract_contact_from_location(location_data)
        assert result["contact_name"] is None
        assert result["contact_phone"] is None

    def test_extract_contact_partial_info(self):
        """Test contact with partial information."""
        location_data = {
            "facility": "Hospital",
            "contacts": [{"name": "Dr. Smith"}]
        }
        result = extract_contact_from_location(location_data)
        assert result["contact_name"] == "Dr. Smith"
        assert result["contact_phone"] is None
