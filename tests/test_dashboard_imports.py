def test_dashboard_data_module_imports():
    # Smoke test: module should import without side effects/errors
    import paos.dashboard.data  # noqa: F401
