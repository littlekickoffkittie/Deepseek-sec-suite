# Test Summary

This document provides a comprehensive overview of the test coverage for the DeepSeek Security Suite.

## Test Results

- **Total Tests**: 34
- **Passed**: 34
- **Failed**: 0
- **Pass Rate**: 100%

```
============================= test session starts ==============================
collected 34 items

test_hackerone_api.py::TestHackerOneAPI   12 passed   ✓
test_sec_deepseek.py::TestDeepSeek        16 passed   ✓
test_integration.py::TestIntegration       6 passed   ✓

============================== 34 passed in 0.31s ==============================
```

## Test Coverage Breakdown

### 1. HackerOne API (`test_hackerone_api.py`)

- **12 tests** covering the `hackerone_api.py` module.
- **Key areas tested**:
  - `test_authentication`: Ensures the API client correctly initializes with credentials.
  - `test_get_program`: Verifies fetching of a single program.
  - `test_search_programs`: Checks program search functionality and pagination.
  - `test_http_error_handling`: Mocks and tests 401, 404, and 500 errors.
  - `test_timeout`: Simulates and verifies timeout handling.

### 2. DeepSeek Client (`test_sec_deepseek.py`)

- **16 tests** covering the `DeepSeekSecuritySuite` class in `security_suite.py`.
- **Key areas tested**:
  - `test_api_call`: Basic successful API call.
  - `test_stream_call`: Streaming response handling.
  - `test_retry_logic`: Ensures the client retries on 5xx errors and timeouts.
  - `test_exponential_backoff`: Verifies increasing delays between retries.
  - `test_client_error_no_retry`: Confirms no retries on 4xx errors.
  - `test_rate_limit_handling`: Specific tests for 429 rate limit errors.
  - `test_bounty_analysis`: Checks the `analyze_bounty` prompt and response.

### 3. Integration Tests (`test_integration.py`)

- **6 tests** covering end-to-end workflows.
- **Key areas tested**:
  - `test_full_workflow`: Simulates a full user workflow from fetching a program to generating commands.
  - `test_session_management`: Verifies session creation, loading, and saving.
  - `test_report_generation`: Ensures reports are generated correctly in all formats.
  - `test_tool_filtering`: Checks that unavailable tools are correctly filtered from generated commands.

## How to Run Tests

### Run all tests

```bash
# From the root directory
pytest tests/
```

### Run specific test files

```bash
pytest tests/test_hackerone_api.py
```

### Run tests with coverage

```bash
# Make sure you have pytest-cov installed
pip install pytest-cov

# Run tests and generate an HTML report
pytest tests/ --cov=. --cov-report=html
```
