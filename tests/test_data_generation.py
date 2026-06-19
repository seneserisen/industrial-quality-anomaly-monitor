import pandas as pd
import pytest

from quality_monitor.data_generation import GenerationConfig, generate_production_data


def test_generation_is_reproducible_and_labelled() -> None:
    config = GenerationConfig(rows=500, machines=3, anomaly_rate=0.06, random_seed=7)
    first = generate_production_data(config)
    second = generate_production_data(config)

    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 500
    assert first["machine_id"].nunique() <= 3
    assert first["is_injected_anomaly"].sum() == 30
    assert set(first["anomaly_type"]) >= {"normal"}


def test_invalid_generation_config_is_rejected() -> None:
    with pytest.raises(ValueError, match="rows"):
        generate_production_data(GenerationConfig(rows=10))
