from platform_sdk.database import DatabasePoolConfig, create_platform_engine, pool_metrics


def test_pool_config_exposes_capacity() -> None:
    config = DatabasePoolConfig(application_name="test-api", pool_size=4, max_overflow=2)

    assert config.maximum_connections == 6


def test_sqlite_engine_uses_safe_metrics_fallbacks() -> None:
    config = DatabasePoolConfig(application_name="test-api", pool_size=4, max_overflow=2)
    engine = create_platform_engine("sqlite:///:memory:", config)

    metrics = pool_metrics(engine, config)

    assert metrics["application_name"] == "test-api"
    assert metrics["configured_maximum_connections"] == 6
    assert isinstance(metrics["checked_out"], int)
    engine.dispose()
