def test_new_finai_api_routes_are_registered():
    from app.main import app
    paths = {route.path for route in app.routes}
    assert "/api/v1/compliance/catalog" in paths
    assert "/api/v1/resources" in paths
    assert "/api/v1/models" in paths
    assert "/api/v1/market/analyst" in paths
    assert "/api/v1/crypto/arbitrage/scan-all" in paths
    assert "/api/v1/system/status" in paths
