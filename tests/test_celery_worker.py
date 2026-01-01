
def test_celery_worker_import():
    """Smoke test to ensure celery_worker imports without error."""
    try:
        import celery_worker
        assert celery_worker.celery is not None
    except ImportError as e:
        pytest.fail(f"Failed to import celery_worker: {e}")
