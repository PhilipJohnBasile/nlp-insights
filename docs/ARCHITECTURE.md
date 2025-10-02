# Architecture Documentation

## System Overview

The Clinical Trials Insights tool follows a modular pipeline architecture with clear separation of concerns.

```
┌─────────────┐
│ CLI/User    │
└──────┬──────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       v                                     v
┌─────────────┐                      ┌────────────┐
│ Data Fetch  │                      │ Streamlit  │
│   Module    │                      │    App     │
└──────┬──────┘                      └─────┬──────┘
       │                                   │
       v                                   │
┌─────────────┐                            │
│   Raw Data  │                            │
│   (JSONL)   │                            │
└──────┬──────┘                            │
       │                                   │
       v                                   │
┌─────────────┐                            │
│ Normalize   │                            │
│   Module    │                            │
└──────┬──────┘                            │
       │                                   │
       v                                   │
┌─────────────┐    ┌─────────────┐        │
│ Eligibility │───▶│  Features   │        │
│   Parser    │    │  Engineer   │        │
└──────┬──────┘    └──────┬──────┘        │
       │                  │               │
       v                  v               │
┌─────────────┐    ┌─────────────┐       │
│  Cleaned    │    │  Clustering │       │
│   Data      │    │   & Risk    │       │
│ (Parquet)   │◀───│   Scoring   │       │
└──────┬──────┘    └─────────────┘       │
       │                                  │
       └──────────────────────────────────┘
```

## Module Breakdown

### 1. Configuration (`config.py`)
- Centralized configuration management
- Environment variable loading
- Path management
- Type-safe config access

### 2. Data Models (`models.py`)
- Pydantic models for type safety
- Data validation
- Serialization/deserialization
- Accessor methods for nested API data

### 3. API Client (`client.py`)
- ClinicalTrials.gov v2 API wrapper
- Response caching
- Rate limiting
- Pagination handling
- Error handling

### 4. Data Pipeline

#### 4.1 Fetch (`fetch.py`)
- Query construction
- Batch retrieval
- JSONL output
- Progress tracking

#### 4.2 Normalize (`normalize.py`)
- Parse raw API responses
- Extract structured fields
- Deduplicate trials
- Parquet output

#### 4.3 Eligibility Parser (`eligibility.py`)
- Age parsing (years/months/weeks)
- Inclusion/exclusion extraction
- Disease stage detection
- Regex-based NLP

#### 4.4 Feature Engineering (`features.py`)
- Numeric encoding
- Date calculations
- Phase/masking encoding
- Multi-site detection

#### 4.5 Clustering (`cluster.py`)
- Feature standardization
- K-means clustering
- Cluster profiling
- Label assignment

#### 4.6 Risk Scoring (`risk.py`)
- Rule-based scoring
- Component penalties
- Threshold configuration
- Transparent methodology

### 5. Web Interface (`app.py`)
- Streamlit UI
- Data loading with caching
- Interactive filtering
- Search and highlighting
- CSV export

## Data Flow

```
Raw API JSON
    ↓
JSONL files (raw/)
    ↓
trials.parquet (normalized metadata)
    ↓
    ├─→ eligibility.parquet (parsed criteria)
    ├─→ features.parquet (numeric features)
    ├─→ clusters.parquet (cluster labels)
    └─→ risks.parquet (risk scores)
         ↓
    Streamlit App (joined view)
```

## Design Principles

### 1. Modularity
- Each module has a single responsibility
- CLI interfaces for all modules
- Modules can run independently

### 2. Reproducibility
- Deterministic operations (seeded random)
- Cached API responses
- Version-controlled configurations

### 3. Type Safety
- Pydantic models for all data structures
- Type hints throughout
- Runtime validation

### 4. Transparency
- Documented risk formulas
- Interpretable features
- Clear data lineage

### 5. Testability
- Unit tests for each module
- Integration tests for pipeline
- Fixtures for sample data

## Technology Choices

### Why Parquet?
- Efficient columnar storage
- Fast read/write
- Schema preservation
- Pandas integration

### Why Pydantic?
- Runtime validation
- Type safety
- JSON serialization
- Documentation via models

### Why Streamlit?
- Rapid prototyping
- Reactive UI
- No frontend code
- Easy deployment

### Why Scikit-learn?
- Production-ready
- Well-documented
- No GPU required
- Deterministic clustering

## Performance Considerations

### Caching Strategy
- API responses cached to disk
- Streamlit data caching with `@st.cache_data`
- No duplicate API calls

### Scaling
- Pipeline processes one trial at a time
- Memory efficient for large datasets
- Parquet enables out-of-core processing

### Rate Limiting
- Configurable delay between requests
- Respects API guidelines
- Can be adjusted per instance

## Extension Points

### Adding New Features
1. Add to `TrialFeatures` model in `models.py`
2. Implement extraction in `features.py`
3. Update tests

### New Risk Components
1. Add penalty field to `TrialRisk` model
2. Implement calculation in `risk.py`
3. Update documentation

### New Data Sources
1. Create new client in `client.py`
2. Add fetch module
3. Normalize to same schema

### Custom Clustering
1. Extend `cluster.py`
2. Add alternative algorithms
3. Compare results

## Security Considerations

- No user authentication (research tool)
- Public data only
- No PII/PHI
- Rate limiting prevents abuse
- Input validation via Pydantic

## Future Enhancements

### Potential Features
- [ ] Semantic search with embeddings
- [ ] Time series analysis
- [ ] Network analysis (collaborations)
- [ ] Export to multiple formats
- [ ] REST API wrapper
- [ ] Scheduled updates
- [ ] Email alerts for new trials

### Scalability
- [ ] Dask for large datasets
- [ ] Database backend (PostgreSQL)
- [ ] Cloud deployment
- [ ] Distributed clustering
