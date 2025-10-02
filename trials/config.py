"""Configuration management for clinical trials analysis."""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://clinicaltrials.gov/api/v2")
    RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))

    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    RAW_DATA_DIR: Path = PROJECT_ROOT / os.getenv("RAW_DATA_DIR", "data/raw")
    CLEAN_DATA_DIR: Path = PROJECT_ROOT / os.getenv("CLEAN_DATA_DIR", "data/clean")

    # Model Configuration
    RANDOM_SEED: int = int(os.getenv("RANDOM_SEED", "42"))
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    CLUSTERING_K: int = int(os.getenv("CLUSTERING_K", "8"))

    # Risk Scoring Thresholds
    SMALL_ENROLLMENT_THRESHOLD: int = int(os.getenv("SMALL_ENROLLMENT_THRESHOLD", "50"))
    LONG_DURATION_DAYS: int = int(os.getenv("LONG_DURATION_DAYS", "730"))
    SINGLE_SITE_PENALTY: int = int(os.getenv("SINGLE_SITE_PENALTY", "10"))

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create necessary directories if they don't exist."""
        cls.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)


config = Config()
