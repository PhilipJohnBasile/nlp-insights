# Testing Guide for Clinical Trials Insights

## Test Suite Overview

This project includes comprehensive unit, integration, and end-to-end tests to ensure code quality and reliability.

### Test Results Summary
- ✅ **195 tests passing**
- ❌ **30 tests failing** (mostly integration tests requiring fixes to match actual implementation)
- 📊 **Test Coverage**: Available in `htmlcov/index.html` after running tests

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and pytest configuration
├── test_validators.py             # Unit tests for input validation
├── test_safety_parser.py          # Unit tests for safety data parsing
├── test_clinical_parser.py        # Unit tests for clinical data parsing
├── test_clinical_features.py      # Unit tests for clinical features
├── test_pipeline_integration.py   # Integration tests for data pipeline
├── test_streamlit_e2e.py          # End-to-end UI workflow tests
├── test_models.py                 # Pydantic model tests (existing)
├── test_eligibility.py            # Eligibility parsing tests (existing)
├── test_features.py               # Feature extraction tests (existing)
├── test_risk.py                   # Risk analysis tests (existing)
└── test_integration.py            # General integration tests (existing)
```

## Running Tests

### Run All Tests
```bash
PYTHONPATH=/Users/pjb/Git/nlp-insights python3 -m pytest tests/ -v
```

### Run Specific Test Categories

**Unit Tests Only:**
```bash
pytest -m unit tests/
```

**Integration Tests:**
```bash
pytest -m integration tests/
```

**End-to-End Tests:**
```bash
pytest -m e2e tests/
```

**Exclude Slow Tests:**
```bash
pytest -m "not slow" tests/
```

### Run Specific Test Files

```bash
# Test validators
pytest tests/test_validators.py -v

# Test safety parser
pytest tests/test_safety_parser.py -v

# Test clinical parser
pytest tests/test_clinical_parser.py -v

# Test pipeline integration
pytest tests/test_pipeline_integration.py -v
```

### Run with Coverage Report

```bash
PYTHONPATH=/Users/pjb/Git/nlp-insights python3 -m pytest tests/ --cov=trials --cov-report=html --cov-report=term-missing
```

View coverage report:
```bash
open htmlcov/index.html
```

## Test Categories

### 1. Unit Tests (test_validators.py)
Tests for input validation functions:
- ✅ Age validation (0-120 years)
- ✅ State validation (US states)
- ✅ NCT ID format validation
- ✅ ECOG status validation (0-4)
- ✅ Text sanitization (XSS/SQL injection prevention)
- ✅ Cancer type validation
- ✅ Prior therapies validation
- ✅ Pagination validation

**Status**: 40/40 tests passing ✅

### 2. Safety Parser Tests (test_safety_parser.py)
Tests for adverse event and toxicity parsing:
- ✅ Common adverse events extraction
- ✅ Dose-limiting toxicity detection
- ⚠️ Grade 3-4 events parsing (2 failures)
- ✅ Safety monitoring requirements
- ✅ Results section toxicity extraction
- ✅ Safety data formatting

**Status**: 28/30 tests passing ⚠️

### 3. Clinical Parser Tests (test_clinical_parser.py)
Tests for eligibility criteria parsing:
- ✅ Inclusion/exclusion splitting
- ✅ Treatment line detection
- ⚠️ Common exclusions checking (4 failures - logic refinement needed)
- ✅ Biomarker requirements parsing
- ✅ Prior therapy limits
- ⚠️ Washout period parsing (1 failure)
- ✅ Required tests extraction
- ⚠️ ECOG requirement parsing (3 failures)

**Status**: 41/50 tests passing ⚠️

### 4. Pipeline Integration Tests (test_pipeline_integration.py)
Tests for complete data processing pipeline:
- ⚠️ Pydantic model validation (attribute naming mismatches)
- ⚠️ Data normalization
- ⚠️ DataFrame conversion
- ✅ Error handling

**Status**: 0/27 tests passing ❌
**Note**: These tests need updating to match actual Pydantic model structure (snake_case vs camelCase)

### 5. Streamlit E2E Tests (test_streamlit_e2e.py)
End-to-end workflow tests:
- Patient matching workflow
- Search and filtering
- Trial details display
- Referral management
- Data export
- Email alerts

**Status**: All tests are placeholders pending Streamlit testing framework setup

## Test Fixtures

### Sample Data Fixtures (conftest.py)
- `sample_trial_json`: Complete trial JSON structure
- `sample_trials_df`: DataFrame with sample trials
- `sample_eligibility_df`: Eligibility criteria data
- `sample_locations_df`: Trial location data
- `sample_clinical_details_df`: Clinical trial details
- `sample_patient_data`: Patient profile for matching
- `sample_eligibility_texts`: Various eligibility text examples

### Using Fixtures in Tests
```python
def test_my_function(sample_trials_df):
    # Use the fixture
    result = my_function(sample_trials_df)
    assert len(result) > 0
```

## Writing New Tests

### Unit Test Template
```python
class TestMyFunction:
    """Test cases for my_function."""

    def test_normal_case(self):
        """Test normal usage."""
        result = my_function("normal input")
        assert result == expected_output

    def test_edge_case(self):
        """Test edge case."""
        result = my_function("")
        assert result is not None

    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            my_function(invalid_input)
```

### Integration Test Template
```python
@pytest.mark.integration
class TestDataPipeline:
    """Integration tests for data pipeline."""

    def test_end_to_end_processing(self, sample_trial_json):
        """Test complete pipeline."""
        # Step 1: Validate
        trial = ClinicalTrial.model_validate(sample_trial_json)

        # Step 2: Normalize
        normalized = normalize_trial(trial)

        # Step 3: Verify
        assert "trial_id" in normalized
```

## Known Issues and Fixes Needed

### High Priority
1. **Pipeline Integration Tests** - Update to use correct attribute names (`protocol_section` not `protocolSection`)
2. **Clinical Parser ECOG** - Fix regex patterns for ECOG requirement detection
3. **Safety Parser Grade Events** - Improve grade 3-4 event extraction patterns

### Medium Priority
4. **Washout Period Parsing** - Add support for day-based patterns
5. **Common Exclusions** - Refine logic for detecting allowed vs excluded conditions
6. **Streamlit E2E Tests** - Implement actual Streamlit testing (requires streamlit >= 1.28.0)

### Low Priority
7. **Test Coverage** - Increase coverage for edge cases
8. **Mock API Responses** - Add comprehensive API mocking for fetch tests

## Continuous Integration

### GitHub Actions (Recommended)
Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: PYTHONPATH=. pytest tests/ --cov=trials
```

## Test-Driven Development Workflow

1. **Write test first** (red phase)
2. **Implement minimal code** to pass test (green phase)
3. **Refactor** while keeping tests passing
4. **Run full suite** before committing

## Performance Testing

For performance benchmarks:
```bash
pytest tests/ --durations=10
```

Shows 10 slowest tests.

## Debugging Failed Tests

### Run single test with detailed output:
```bash
pytest tests/test_validators.py::TestValidateAge::test_valid_age -vv -s
```

### Run with Python debugger on failure:
```bash
pytest tests/test_validators.py --pdb
```

### Show local variables on failure:
```bash
pytest tests/test_validators.py -l
```

## Test Quality Metrics

### Current Metrics
- **Code Coverage**: ~65% (estimated, run coverage report for exact)
- **Test Count**: 225 total tests
- **Pass Rate**: 87% (195/225)
- **Average Test Time**: <2ms per test
- **Total Suite Time**: ~2.6 seconds

### Coverage Goals
- Unit Tests: 90%+ coverage
- Integration Tests: 70%+ coverage
- E2E Tests: Critical user paths only

## Best Practices

1. ✅ **One assertion per test** (when possible)
2. ✅ **Test names describe behavior** (`test_validate_age_rejects_negative`)
3. ✅ **Use fixtures for setup** (avoid repetitive code)
4. ✅ **Mock external dependencies** (APIs, databases)
5. ✅ **Keep tests fast** (<100ms per test)
6. ✅ **Test error cases** (not just happy path)
7. ✅ **Use markers** to categorize tests
8. ✅ **Document complex test logic**

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Streamlit Testing](https://docs.streamlit.io/develop/api-reference/app-testing)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Contributing Tests

When adding new features:
1. Write tests first (TDD approach)
2. Ensure new code has >80% test coverage
3. Add integration test if touching multiple modules
4. Update this documentation if adding new test categories
5. Run full test suite before submitting PR

## Quick Reference

```bash
# Fast test run (unit tests only)
pytest -m unit tests/

# Before commit (all tests except slow)
pytest -m "not slow" tests/

# Full test suite with coverage
PYTHONPATH=. pytest tests/ --cov=trials --cov-report=html

# Debug specific failure
pytest tests/test_file.py::TestClass::test_method -vv --pdb

# Update snapshots (if using snapshot testing)
pytest tests/ --snapshot-update
```

---

**Last Updated**: October 3, 2025
**Test Suite Version**: 1.0.0
**Pytest Version**: 8.4.2
