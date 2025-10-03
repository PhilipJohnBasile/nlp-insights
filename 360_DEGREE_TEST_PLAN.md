# 360° Test Coverage Plan

## Current Coverage Analysis

### ✅ Well-Tested Modules (100% coverage)
1. **trials/validators.py** - 40 tests
2. **trials/safety_parser.py** - 30 tests
3. **trials/clinical_parser.py** - 50 tests
4. **trials/clinical_data.py** - 78 tests (via test_clinical_features.py)
5. **UI (app.py)** - 22 Playwright tests

### ⚠️ Partially Tested Modules (existing but incomplete)
1. **trials/models.py** - Basic tests only (test_models.py)
2. **trials/normalize.py** - Integration tests only
3. **trials/eligibility.py** - Minimal coverage
4. **trials/features.py** - Minimal coverage
5. **trials/risk.py** - Basic tests only

### ❌ Untested Modules (0% coverage)
**High Priority:**
1. **trials/email_alerts.py** - Email notification system
2. **trials/emr_integration.py** - EMR data integration
3. **trials/enrollment_tracker.py** - Patient enrollment tracking
4. **trials/referral_tracker.py** - Referral management
5. **trials/financial_info.py** - Trial cost/insurance info
6. **trials/protocol_access.py** - Protocol document access
7. **trials/similar_patients.py** - Patient matching algorithms
8. **trials/trial_card_enhancer.py** - Trial card rendering
9. **trials/search_profiles.py** - Saved search profiles
10. **trials/trial_notes.py** - Clinical notes management

**Medium Priority:**
11. **trials/mobile_styles.py** - Mobile CSS/styling
12. **trials/enhance_clinical.py** - Clinical data enhancement
13. **trials/enhance_eligibility.py** - Eligibility enhancement
14. **trials/process_manager.py** - Background process management

**Low Priority:**
15. **trials/client.py** - API client (external dependency)
16. **trials/fetch.py** - Data fetching utilities
17. **trials/cluster.py** - Trial clustering algorithms
18. **trials/config.py** - Configuration management

---

## Recommended Test Suites for 360° Coverage

### Suite 1: Email & Notifications Tests ⭐⭐⭐
**File**: `tests/test_email_alerts.py`
**Priority**: HIGH
**Module**: trials/email_alerts.py

**Why**: Critical for user engagement, potential for bugs in email formatting/delivery

**Test Categories**:
- Email template rendering (HTML/plain text)
- Alert trigger conditions (new trials, status changes)
- User preference management (opt-in/opt-out, frequency)
- Email validation and sanitization
- Mock SMTP server integration
- Batch email sending
- Error handling (invalid emails, SMTP failures)
- Rate limiting

**Estimated Tests**: 30-40 tests
**Example Tests**:
```python
def test_format_trial_alert_email()
def test_send_new_trial_notification()
def test_respect_user_email_preferences()
def test_handle_invalid_email_address()
def test_batch_send_daily_digest()
def test_unsubscribe_link_generation()
```

---

### Suite 2: EMR Integration Tests ⭐⭐⭐
**File**: `tests/test_emr_integration.py`
**Priority**: HIGH
**Module**: trials/emr_integration.py

**Why**: Critical for clinical workflows, HIPAA compliance, data security

**Test Categories**:
- HL7/FHIR message parsing
- Patient data extraction
- Data mapping (EMR → app format)
- Authentication/authorization
- Data sanitization and validation
- Error handling (malformed messages, missing data)
- Security (PHI handling, encryption)
- Mock EMR responses

**Estimated Tests**: 35-45 tests
**Example Tests**:
```python
def test_parse_hl7_patient_demographics()
def test_extract_diagnosis_codes()
def test_map_emr_labs_to_biomarkers()
def test_handle_missing_patient_data()
def test_sanitize_phi_in_logs()
def test_authenticate_emr_connection()
```

---

### Suite 3: Enrollment & Referral Tracking Tests ⭐⭐⭐
**File**: `tests/test_enrollment_referral.py`
**Priority**: HIGH
**Modules**: trials/enrollment_tracker.py, trials/referral_tracker.py

**Why**: Core workflow functionality, tracks patient journey

**Test Categories**:
- Patient enrollment status transitions
- Referral creation and routing
- Status updates (referred → enrolled → completed)
- Notification triggers
- Data persistence
- Duplicate detection
- Workflow validation
- Reporting/analytics

**Estimated Tests**: 40-50 tests
**Example Tests**:
```python
def test_create_referral_for_trial()
def test_update_enrollment_status()
def test_track_referral_lifecycle()
def test_prevent_duplicate_enrollments()
def test_notify_on_status_change()
def test_generate_enrollment_report()
```

---

### Suite 4: Financial & Protocol Tests ⭐⭐
**File**: `tests/test_financial_protocol.py`
**Priority**: MEDIUM
**Modules**: trials/financial_info.py, trials/protocol_access.py

**Why**: Important for patient decision-making, document management

**Test Categories**:
- Insurance coverage estimation
- Cost calculation (travel, procedures)
- Financial assistance lookup
- Protocol document parsing
- Access control (authorized users only)
- Document versioning
- PDF/document rendering

**Estimated Tests**: 25-35 tests
**Example Tests**:
```python
def test_estimate_trial_costs()
def test_check_insurance_coverage()
def test_find_financial_assistance()
def test_parse_protocol_pdf()
def test_restrict_protocol_access()
def test_track_document_versions()
```

---

### Suite 5: Patient Matching & Similarity Tests ⭐⭐⭐
**File**: `tests/test_patient_matching.py`
**Priority**: HIGH
**Module**: trials/similar_patients.py

**Why**: Core algorithm, affects match quality and user satisfaction

**Test Categories**:
- Similarity scoring algorithms
- Feature weighting (demographics, biomarkers, diagnosis)
- Edge cases (missing data, rare conditions)
- Performance (large patient cohorts)
- Ranking/sorting logic
- Privacy (anonymization)

**Estimated Tests**: 30-40 tests
**Example Tests**:
```python
def test_calculate_patient_similarity_score()
def test_match_by_biomarker_profile()
def test_handle_missing_patient_features()
def test_rank_similar_patients()
def test_anonymize_patient_data()
def test_performance_with_1000_patients()
```

---

### Suite 6: Search Profiles & Notes Tests ⭐⭐
**File**: `tests/test_search_notes.py`
**Priority**: MEDIUM
**Modules**: trials/search_profiles.py, trials/trial_notes.py

**Why**: User productivity features, data persistence

**Test Categories**:
- Profile creation/update/delete (CRUD)
- Profile serialization (JSON)
- Search criteria validation
- Notes creation with rich text
- Notes tagging and categorization
- Search and filtering
- Data export

**Estimated Tests**: 25-30 tests
**Example Tests**:
```python
def test_save_search_profile()
def test_load_and_apply_profile()
def test_delete_search_profile()
def test_create_trial_note()
def test_tag_notes_with_categories()
def test_search_notes_by_keyword()
```

---

### Suite 7: Trial Card UI Tests ⭐⭐
**File**: `tests/test_trial_card_rendering.py`
**Priority**: MEDIUM
**Module**: trials/trial_card_enhancer.py

**Why**: Visual presentation layer, user experience

**Test Categories**:
- Card rendering with all data types
- Conditional display (missing data)
- Badge generation (status, phase)
- Link generation
- Responsive layout
- Accessibility (ARIA labels)

**Estimated Tests**: 20-25 tests
**Example Tests**:
```python
def test_render_complete_trial_card()
def test_handle_missing_trial_fields()
def test_generate_status_badge()
def test_create_contact_link()
def test_responsive_card_layout()
```

---

### Suite 8: Data Enhancement & Normalization Tests ⭐⭐
**File**: `tests/test_data_enhancement.py`
**Priority**: MEDIUM
**Modules**: trials/enhance_clinical.py, trials/enhance_eligibility.py, trials/normalize.py

**Why**: Data quality impacts match accuracy

**Test Categories**:
- Clinical data enrichment
- Eligibility text normalization
- Data cleaning (whitespace, special chars)
- Standardization (units, formats)
- Missing data imputation
- Duplicate detection

**Estimated Tests**: 30-35 tests
**Example Tests**:
```python
def test_normalize_clinical_terms()
def test_standardize_biomarker_names()
def test_clean_eligibility_text()
def test_convert_measurement_units()
def test_detect_duplicate_trials()
```

---

### Suite 9: Integration & API Tests ⭐⭐⭐
**File**: `tests/test_api_integration.py`
**Priority**: HIGH
**Modules**: trials/client.py, trials/fetch.py

**Why**: External dependencies, network reliability

**Test Categories**:
- ClinicalTrials.gov API requests
- Response parsing (JSON/XML)
- Rate limiting
- Retry logic
- Error handling (timeout, 500 errors)
- Mock API responses
- Pagination handling
- Query parameter validation

**Estimated Tests**: 30-40 tests
**Example Tests**:
```python
def test_fetch_trials_from_api()
def test_handle_api_rate_limit()
def test_retry_failed_requests()
def test_parse_api_response()
def test_handle_network_timeout()
def test_paginate_large_result_sets()
```

---

### Suite 10: Performance & Load Tests ⭐⭐
**File**: `tests/test_performance.py`
**Priority**: MEDIUM
**All Modules**

**Why**: Scalability, user experience under load

**Test Categories**:
- Search performance (1k, 10k, 100k trials)
- Parsing performance (large eligibility texts)
- Memory usage profiling
- Database query optimization
- Concurrent user simulation
- Cache effectiveness

**Estimated Tests**: 15-20 tests
**Example Tests**:
```python
def test_search_performance_with_10k_trials()
def test_parse_performance_large_text()
def test_memory_usage_stays_below_threshold()
def test_concurrent_user_searches()
def test_cache_hit_rate()
```

---

### Suite 11: Security & Compliance Tests ⭐⭐⭐
**File**: `tests/test_security.py`
**Priority**: HIGH
**All Modules**

**Why**: HIPAA compliance, data protection, user trust

**Test Categories**:
- SQL injection prevention
- XSS attack prevention (already in validators)
- Authentication/authorization
- Session management
- PHI encryption at rest/transit
- Audit logging
- Access control
- Data anonymization

**Estimated Tests**: 25-30 tests
**Example Tests**:
```python
def test_prevent_sql_injection()
def test_sanitize_user_input()
def test_encrypt_patient_data()
def test_enforce_role_based_access()
def test_log_phi_access_events()
def test_session_timeout()
```

---

### Suite 12: Data Pipeline End-to-End Tests ⭐⭐
**File**: `tests/test_pipeline_e2e.py`
**Priority**: MEDIUM
**Module**: trials/process_manager.py + others

**Why**: Complete workflow validation

**Test Categories**:
- Full data pipeline (fetch → parse → enhance → store)
- Multi-step workflows
- Error recovery
- Data consistency checks
- Transaction handling
- Rollback scenarios

**Estimated Tests**: 20-25 tests
**Example Tests**:
```python
def test_complete_trial_import_pipeline()
def test_pipeline_error_recovery()
def test_data_consistency_after_pipeline()
def test_rollback_on_validation_failure()
```

---

### Suite 13: Mobile & Accessibility Tests ⭐
**File**: `tests/test_mobile_a11y.py`
**Priority**: LOW-MEDIUM
**Modules**: trials/mobile_styles.py, trials/app.py

**Why**: Accessibility compliance, mobile user experience

**Test Categories**:
- Mobile viewport rendering
- Touch interactions
- Screen reader compatibility
- Keyboard navigation
- WCAG 2.1 compliance
- Color contrast
- Focus management

**Estimated Tests**: 20-25 tests (Playwright)
**Example Tests**:
```python
def test_mobile_navigation_touch()
def test_screen_reader_labels()
def test_keyboard_only_navigation()
def test_color_contrast_ratio()
def test_focus_trap_in_modals()
```

---

## Implementation Priority Matrix

### Phase 1: Critical Business Logic (Weeks 1-2)
**Est. 140-180 tests**
1. ✅ EMR Integration Tests (35-45)
2. ✅ Enrollment & Referral Tests (40-50)
3. ✅ Patient Matching Tests (30-40)
4. ✅ API Integration Tests (30-40)

### Phase 2: User Features (Weeks 3-4)
**Est. 110-145 tests**
5. ✅ Email & Notifications Tests (30-40)
6. ✅ Financial & Protocol Tests (25-35)
7. ✅ Search Profiles & Notes Tests (25-30)
8. ✅ Data Enhancement Tests (30-35)

### Phase 3: Quality & Security (Week 5)
**Est. 65-80 tests**
9. ✅ Security & Compliance Tests (25-30)
10. ✅ Performance Tests (15-20)
11. ✅ Trial Card Rendering Tests (20-25)

### Phase 4: Complete Coverage (Week 6)
**Est. 40-50 tests**
12. ✅ Pipeline E2E Tests (20-25)
13. ✅ Mobile & A11y Tests (20-25)

---

## Total Additional Tests Needed

**Current**: 247 tests (100% pass)
**Recommended Additional**: ~355-455 tests
**Total Target**: ~600-700 tests

### Coverage Goal
- **Unit Tests**: ~500 tests (80%)
- **Integration Tests**: ~100 tests (15%)
- **E2E/UI Tests**: ~50 tests (5%)
- **Performance Tests**: ~20 tests
- **Security Tests**: ~30 tests

### Expected Coverage Metrics
- **Overall Code Coverage**: 80%+ (from 23%)
- **Critical Paths Coverage**: 100%
- **Business Logic Coverage**: 95%+
- **UI Coverage**: 90%+

---

## Quick Wins (Start Here)

### Week 1 Quick Wins (4-6 hours each)
1. **test_search_notes.py** - Simple CRUD operations, low complexity
2. **test_trial_card_rendering.py** - Template/UI logic, straightforward
3. **test_data_enhancement.py** - Text processing, similar to existing parsers

### High-Impact Tests (2-3 days each)
4. **test_emr_integration.py** - Complex but critical
5. **test_enrollment_referral.py** - Core workflow
6. **test_patient_matching.py** - Core algorithm

---

## Testing Tools & Frameworks Needed

### Already Installed ✅
- pytest
- pytest-cov
- pytest-mock
- pytest-playwright

### Recommended Additions
```bash
pip install pytest-benchmark      # Performance testing
pip install pytest-timeout        # Prevent hanging tests
pip install pytest-xdist          # Parallel test execution
pip install faker                 # Generate test data
pip install freezegun             # Time/date mocking
pip install responses             # Mock HTTP requests
pip install pytest-asyncio        # Async test support
pip install locust                # Load testing
pip install pytest-html           # HTML test reports
pip install axe-playwright        # Accessibility testing
```

---

## Success Metrics

### Coverage Metrics
- [ ] 80% overall code coverage
- [ ] 100% coverage on validators, parsers, core algorithms
- [ ] 90% coverage on user-facing features
- [ ] 70% coverage on integrations

### Quality Metrics
- [ ] 100% test pass rate maintained
- [ ] 0 critical bugs in production
- [ ] < 2 minute total test execution time
- [ ] < 5% flaky test rate

### Compliance Metrics
- [ ] All HIPAA-related code tested
- [ ] Security vulnerabilities tested
- [ ] WCAG 2.1 AA compliance verified
- [ ] API rate limits validated

---

## Next Steps

1. **Review & Prioritize**: Discuss with team which modules are most critical
2. **Set Up Tools**: Install recommended testing tools
3. **Create Templates**: Establish test file templates for consistency
4. **Implement Phase 1**: Focus on critical business logic (EMR, enrollment, matching)
5. **Monitor Coverage**: Track coverage metrics weekly
6. **Iterate**: Adjust priorities based on production issues

---

**Created**: October 3, 2025
**Current Tests**: 247 (100% passing)
**Target Tests**: 600-700
**Estimated Effort**: 6 weeks (1 engineer full-time)
**Priority**: Start with EMR, Enrollment, and Patient Matching tests
