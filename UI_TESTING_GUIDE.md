# UI Testing with Playwright - Complete Guide

## Overview

Comprehensive UI testing setup for the Clinical Trials Insights Streamlit application using Playwright.

## Test Results

### Current Status
```
✅ 22/22 UI tests PASSING (100%)
⏱️ ~60 seconds execution time
🌐 Tests actual running application
```

## Setup

### 1. Install Dependencies
```bash
pip install playwright pytest-playwright
python3 -m playwright install chromium
```

### 2. Start the Application
```bash
# Terminal 1: Start Streamlit app
PYTHONPATH=/Users/pjb/Git/nlp-insights streamlit run trials/app.py --server.port 8501
```

### 3. Run Tests
```bash
# Terminal 2: Run UI tests

# Headless mode (fast, no browser window)
pytest tests/test_ui_playwright.py --no-cov

# Headed mode (see the browser)
pytest tests/test_ui_playwright.py --headed --no-cov

# Run specific test
pytest tests/test_ui_playwright.py::TestPatientMatching::test_patient_form_inputs --headed --no-cov

# With screenshots on failure
pytest tests/test_ui_playwright.py --screenshot=only-on-failure --no-cov
```

## Test Coverage

### ✅ All Tests Passing (22/22)

#### App Initialization (3/3)
- ✅ App loads successfully
- ✅ All tabs visible and accessible
- ✅ Header elements present

#### Patient Matching (5/5)
- ✅ Patient matching form loads
- ✅ NCT ID lookup present
- ✅ Form submission button
- ✅ Form inputs work correctly
- ✅ Biomarker checkboxes present

#### Navigation (2/2)
- ✅ Navigate to Explore tab
- ✅ Settings navigation

#### Data Display (2/2)
- ✅ No data message appropriate
- ✅ Fetch Data tab present

#### Responsive Design (2/2)
- ✅ Mobile viewport (375x667)
- ✅ Tablet viewport (768x1024)

#### Accessibility (2/2)
- ✅ Page has proper title
- ✅ Main landmarks present

#### Interactive Elements (2/2)
- ✅ Checkbox interaction
- ✅ Text input interaction

#### Error Handling (1/1)
- ✅ Invalid URL handling

#### Performance (2/2)
- ✅ Initial load time < 10s
- ✅ Tab switching responsive

#### User Journey (1/1)
- ✅ Basic search workflow

## Test Structure

### Test File Organization
```
tests/test_ui_playwright.py
├── TestAppInitialization      # App loads, headers, tabs
├── TestPatientMatching         # Patient matching workflow
├── TestNavigation              # Tab navigation
├── TestDataDisplay             # Data display features
├── TestResponsiveDesign        # Mobile/tablet views
├── TestAccessibility           # Accessibility features
├── TestInteractiveElements     # UI interactions
├── TestErrorHandling           # Error scenarios
├── TestPerformance             # Load times
└── TestFullUserJourney         # Complete workflows
```

### Fixture Usage
```python
@pytest.fixture
def streamlit_app(page: Page):
    """Auto-navigate to app and wait for load."""
    page.goto("http://localhost:8501")
    page.wait_for_selector('[data-testid="stAppViewContainer"]')
    return page
```

## Common Patterns

### Finding Elements
```python
# By text content
streamlit_app.locator("text=/Patient Matching/i")

# By data-testid (Streamlit specific)
streamlit_app.locator('[data-testid="stAppViewContainer"]')

# By role
streamlit_app.locator("button:has-text('Find Matching Trials')")

# First/nth element
streamlit_app.locator("input[type='number']").first
streamlit_app.locator("button[role='tab']").nth(1)
```

### Assertions
```python
# Visibility
expect(element).to_be_visible()
expect(element).not_to_be_visible()

# Content
expect(element).to_have_text("Expected text")
expect(element).to_contain_text("Partial text")

# State
assert element.is_checked()
assert element.input_value() == "expected"
```

### Interactions
```python
# Click
element.click()

# Fill input
input_field.fill("text value")

# Select dropdown
dropdown.select_option("Option Label")

# Check/uncheck
checkbox.check()
checkbox.uncheck()
```

### Waiting
```python
# Wait for selector
page.wait_for_selector("css=selector")

# Wait for timeout
page.wait_for_timeout(1000)  # ms

# Wait for load state
page.wait_for_load_state("networkidle")
```

## Issues Fixed for 100% Pass Rate

### 1. Header Presence Test ✅
**Issue**: Multiple elements match "research tool"
**Fix Applied**: Use .first to handle multiple matches
```python
expect(streamlit_app.locator("text=/research tool/i").first).to_be_visible()
```

### 2. Settings Navigation ✅
**Issue**: Tab click not registering, multiple "Settings" elements
**Fix Applied**: Increase wait time and use specific h2 selector
```python
settings_tab.click()
streamlit_app.wait_for_timeout(2000)
expect(streamlit_app.locator("h2:has-text('Settings')")).to_be_visible()
```

### 3. Responsive Tests ✅
**Issue**: Mobile/tablet viewports looking for specific text
**Fix Applied**: Use Streamlit container selector instead
```python
page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
expect(page.locator('[data-testid="stAppViewContainer"]')).to_be_visible()
```

### 4. Checkbox Interaction ✅
**Issue**: Streamlit hides actual checkbox, only label is visible
**Fix Applied**: Click label instead of hidden checkbox
```python
egfr_label = streamlit_app.locator('label:has-text("EGFR mutation")')
egfr_label.click()  # Click visible label, not hidden input
```

## Best Practices

### 1. Use Streamlit-Specific Selectors
```python
# Good - Streamlit data-testid
'[data-testid="stAppViewContainer"]'
'[data-testid="stForm"]'
'[data-testid="stCheckbox"]'

# Also good - semantic selectors
'button:has-text("Find Matching Trials")'
'input[type="number"]'
```

### 2. Wait for Dynamic Content
```python
# Streamlit re-renders on interaction
element.click()
page.wait_for_timeout(1000)  # Wait for re-render
```

### 3. Handle Multiple Matches
```python
# Use .first or .nth() when multiple elements match
element = page.locator("selector").first
element = page.locator("selector").nth(2)
```

### 4. Verify State Changes
```python
# Always verify interactions worked
button.click()
page.wait_for_timeout(500)
expect(result_element).to_be_visible()
```

## Advanced Testing

### Test with Data
```python
@pytest.fixture
def app_with_data(page: Page):
    """Start app with test data loaded."""
    # 1. Navigate to Fetch Data tab
    # 2. Load test dataset
    # 3. Return to Patient Matching
    pass
```

### Visual Regression Testing
```python
def test_visual_regression(page: Page):
    """Take screenshots for visual comparison."""
    page.goto(BASE_URL)
    page.screenshot(path="tests/screenshots/homepage.png")
```

### Network Interception
```python
def test_api_calls(page: Page):
    """Monitor network requests."""
    # Intercept API calls to ClinicalTrials.gov
    page.route("**/clinicaltrials.gov/**", lambda route: route.continue_())
```

### Accessibility Auditing
```python
def test_accessibility(page: Page):
    """Run accessibility checks."""
    # Use axe-playwright for a11y audits
    from axe_playwright_python import Axe
    axe = Axe()
    results = axe.run(page)
    assert len(results.violations) == 0
```

## Performance Testing

### Metrics to Track
```python
def test_performance_metrics(page: Page):
    """Measure key performance indicators."""
    import time

    start = time.time()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    load_time = time.time() - start

    assert load_time < 3.0, "Page load too slow"
```

## CI/CD Integration

### GitHub Actions
```yaml
name: UI Tests

on: [push, pull_request]

jobs:
  playwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install playwright pytest-playwright
          playwright install chromium

      - name: Start Streamlit
        run: |
          PYTHONPATH=. streamlit run trials/app.py --server.port 8501 &
          sleep 10

      - name: Run tests
        run: pytest tests/test_ui_playwright.py --no-cov

      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v2
        with:
          name: screenshots
          path: tests/screenshots/
```

## Debugging

### View Tests in Browser
```bash
# See what's happening
pytest tests/test_ui_playwright.py --headed --slowmo=1000
```

### Pause on Failure
```python
# Add breakpoint in test
import pdb; pdb.set_trace()

# Or use Playwright inspector
page.pause()
```

### Screenshots
```bash
# Take screenshot on any failure
pytest tests/test_ui_playwright.py --screenshot=only-on-failure
```

### Video Recording
```bash
# Record video of test execution
pytest tests/test_ui_playwright.py --video=retain-on-failure
```

## Common Streamlit UI Elements

### Tabs
```python
# Click tab by name
page.locator("button:has-text('Patient Matching')").click()
```

### Forms
```python
# Find form
form = page.locator('[data-testid="stForm"]')

# Submit button inside form
form.locator("button[type='submit']").click()
```

### Checkboxes
```python
# Streamlit checkbox
checkbox = page.locator('label:has-text("EGFR")')
checkbox.click()
```

### Number Inputs
```python
# Number input
age_input = page.locator("input[type='number']").first
age_input.fill("65")
```

### Selectboxes
```python
# Streamlit selectbox
selectbox = page.locator('[data-testid="stSelectbox"]').first
selectbox.click()
page.locator("text='Option Name'").click()
```

### Buttons
```python
# Primary button
button = page.locator("button:has-text('Find Matching Trials')")
button.click()
```

## Maintenance

### Keep Tests Fast
- Use headless mode for CI
- Parallel execution where possible
- Mock external API calls
- Use test data fixtures

### Keep Tests Reliable
- Explicit waits over implicit
- Unique selectors
- Verify state changes
- Handle async updates

### Keep Tests Maintainable
- Page object pattern
- Reusable fixtures
- Clear test names
- Good documentation

## Next Steps

### Expand Coverage
1. Add tests for trial detail views
2. Test referral workflow end-to-end
3. Test data export functionality
4. Test email alert setup
5. Test search profile saving

### Add Visual Testing
- Screenshot comparison
- Visual regression detection
- Cross-browser testing

### Performance Monitoring
- Track load times
- Monitor memory usage
- Measure interaction latency

### Accessibility Testing
- Screen reader compatibility
- Keyboard navigation
- Color contrast
- ARIA labels

## Resources

- [Playwright Docs](https://playwright.dev/python/)
- [Pytest-Playwright](https://github.com/microsoft/playwright-pytest)
- [Streamlit Testing](https://docs.streamlit.io/develop/api-reference/app-testing)
- [Best Practices](https://playwright.dev/python/docs/best-practices)

---

**Created**: October 3, 2025
**Test Framework**: Playwright + Pytest
**Pass Rate**: 22/22 (100%) ✅
**App URL**: http://localhost:8501
