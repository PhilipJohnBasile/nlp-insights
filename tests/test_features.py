"""Tests for feature engineering."""

from trials.features import encode_masking, encode_phase


def test_encode_phase():
    """Test phase encoding."""
    assert encode_phase("Phase 1") == 2
    assert encode_phase("Phase 2") == 3
    assert encode_phase("Phase 3") == 4
    assert encode_phase("Early Phase 1") == 1
    assert encode_phase(None) == 0


def test_encode_masking():
    """Test masking encoding."""
    assert encode_masking("Quadruple") == 4
    assert encode_masking("Triple") == 3
    assert encode_masking("Double") == 2
    assert encode_masking("Single") == 1
    assert encode_masking("None") == 0
    assert encode_masking(None) == 0
