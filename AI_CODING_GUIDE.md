# AI Coding Guide: How This Project Was Optimized

This document explains how this project was structured for optimal AI-assisted coding.

## Design Principles for AI Coding

### 1. Modular Architecture

Each module has a **single, clear responsibility**:

```
src/ingestion/gtfs_rt_parser.py      → Parse GTFS-RT feeds
src/ingestion/data_quality.py        → Validate data
src/ingestion/s3_uploader.py         → Upload to S3
src/processing/delay_calculator.py   → Calculate delays
```

**Why this works for AI:**
- AI can modify one module without affecting others
- Clear prompts: "Update the delay calculator to handle edge cases"
- Easy to test individual components

### 2. Self-Documenting Code

Every file starts with a clear docstring:

```python
"""
GTFS Real-Time protobuf parser for Edmonton Transit System.
Parses Vehicle Positions and Trip Updates feeds.
"""
```

Every function has type hints and docstrings:

```python
def parse_vehicle_positions(self) -> List[Dict]:
    """
    Parse Vehicle Positions feed into structured records.
    
    Returns:
        List of dictionaries with vehicle position data
    """
```

**Why this works for AI:**
- AI understands context immediately
- Can generate accurate modifications
- Easier to maintain consistency

### 3. Configuration Centralization

All config in one place (`src/utils/config.py`):

```python
AWS_ACCESS_KEY_ID = get_config('AWS_ACCESS_KEY_ID')
S3_BUCKET_NAME = get_config('S3_BUCKET_NAME')
```

**Why this works for AI:**
- Single source of truth
- Easy to prompt: "Add a new config variable for X"
- Reduces duplication bugs

### 4. Testable Design

Each module has tests in parallel structure:

```
src/ingestion/gtfs_rt_parser.py
tests/test_ingestion.py
```

**Why this works for AI:**
- Can prompt: "Add tests for the new feature"
- AI knows where tests belong
- Maintains test coverage

### 5. Clear Data Schemas

Data structures documented in docstrings:

```python
record = {
    'vehicle_id': vehicle.vehicle.id,    # Unique vehicle identifier
    'trip_id': vehicle.trip.trip_id,     # Current trip ID
    'latitude': vehicle.position.latitude,
    'longitude': vehicle.position.longitude,
    # ...
}
```

**Why this works for AI:**
- AI understands expected data format
- Can generate transformations accurately
- Easier to catch type mismatches

## Prompting Strategies

### Strategy 1: File-Scoped Prompts

✅ **Good:** "Update `src/ingestion/gtfs_rt_parser.py` to add error handling for network timeouts"

❌ **Bad:** "Make the parser more robust"

### Strategy 2: Provide Context

✅ **Good:** "The delay is calculated in `delay_calculator.py` by comparing real-time arrival_delay with scheduled times. Add a function to calculate on-time rate (percentage within 5 minutes)"

❌ **Bad:** "Add an on-time rate metric"

### Strategy 3: Reference Existing Patterns

✅ **Good:** "Add a new dashboard component similar to `components/kpi_cards.py` that shows hourly trends"

❌ **Bad:** "Add a trends chart"

### Strategy 4: Specify Output Format

✅ **Good:** "Create a function that returns a pandas DataFrame with columns: route_id, avg_delay, on_time_rate"

❌ **Bad:** "Make a function that analyzes routes"

## Common AI Coding Workflows

### Workflow 1: Add New Feature

1. **Prompt:** "I want to add weather integration as an ML feature"
2. **AI Response:** Suggests modifying `feature_engineer.py` and `weather.py`
3. **Prompt:** "Show me the exact code changes for `feature_engineer.py`"
4. **AI Response:** Provides diff with context
5. **Prompt:** "Add tests for the weather feature in `tests/test_processing.py`"

### Workflow 2: Fix Bug

1. **Prompt:** "The delay calculation is returning negative values. The logic is in `delay_calculator.py`, lines 45-60"
2. **AI Response:** Analyzes the logic, identifies issue
3. **Prompt:** "Fix the issue and add validation to ensure delays are reasonable"
4. **AI Response:** Provides corrected code with validation

### Workflow 3: Refactor

1. **Prompt:** "The `lambda_handler.py` is getting long. Extract the DynamoDB writing logic into a separate function"
2. **AI Response:** Provides refactored code
3. **Prompt:** "Update the tests to cover the new function"

## Project-Specific AI Prompts

### For This Project

**Data Ingestion:**
```
"Update src/ingestion/gtfs_rt_parser.py to handle empty feeds gracefully by returning empty lists instead of throwing exceptions"
```

**Feature Engineering:**
```
"Add a new feature 'distance_from_downtown' to feature_engineer.py using the Haversine formula. Downtown Edmonton coordinates are (53.5461, -113.4937)"
```

**Dashboard:**
```
"Add a new component to dashboard/components/ that shows a time series of average delays over the last 24 hours using Plotly line chart"
```

**ML Model:**
```
"In train_model.py, add hyperparameter tuning using GridSearchCV for the RandomForestRegressor with parameters: n_estimators [50, 100, 200], max_depth [10, 20, 30]"
```

## Best Practices

### 1. One Change at a Time

✅ Do: "Add error logging to the Lambda handler"
❌ Don't: "Add error logging, improve performance, and refactor the entire module"

### 2. Specify the "Why"

✅ Do: "Add retry logic to S3 uploads because network failures are common in Lambda"
❌ Don't: "Add retry logic"

### 3. Request Validation

✅ Do: "After adding the feature, show me how to test it"
❌ Don't: Add feature and move on without testing

### 4. Ask for Documentation

✅ Do: "Update the docstring and add inline comments explaining the algorithm"
❌ Don't: Leave undocumented code

## AI Limitations & Workarounds

### Limitation 1: No Real-Time API Access

**Problem:** AI can't test live GTFS-RT feeds

**Workaround:** 
```python
# Add mock data generators
def _load_mock_vehicle_positions(self) -> pd.DataFrame:
    """Generate mock data for testing."""
    # Sample implementation
```

### Limitation 2: AWS Credentials

**Problem:** AI can't access your AWS account

**Workaround:**
- Use `.env.example` template
- Test locally with mocks first
- Deploy manually or via CI/CD

### Limitation 3: Large Context

**Problem:** AI may lose context with many files

**Workaround:**
- Reference specific files in prompts
- Use clear module boundaries
- Keep functions under 50 lines

## Iterative Development with AI

### Phase 1: Scaffold
```
"Create a basic GTFS-RT parser with placeholder functions"
```

### Phase 2: Implement Core
```
"Implement the parse_vehicle_positions function to parse protobuf data"
```

### Phase 3: Add Error Handling
```
"Add try-except blocks and logging to handle parsing errors"
```

### Phase 4: Optimize
```
"Optimize the parser to reduce memory usage for large feeds"
```

### Phase 5: Test & Document
```
"Add unit tests and update docstrings"
```

## Conclusion

This project was built with AI-coding-first principles:

- **Modular:** Easy to modify individual components
- **Documented:** AI understands context immediately
- **Testable:** Each change can be validated
- **Configurable:** Settings centralized for easy changes
- **Clear:** Explicit schemas and type hints

Following these patterns, you can efficiently use AI assistants to:
- Add new features
- Fix bugs
- Refactor code
- Write tests
- Generate documentation

**Remember:** Good code structure makes both humans and AI more productive!
