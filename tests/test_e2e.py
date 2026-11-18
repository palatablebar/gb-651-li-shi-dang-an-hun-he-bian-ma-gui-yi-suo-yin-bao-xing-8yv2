def test_all_module_pages(client):
    for path in ['/intake', '/encoding', '/fields', '/content', '/reconcile', '/runs']:
        response = client.get(path)
        assert response.status_code == 200
        assert "panel" in response.text

def test_all_module_apis_and_idempotent_run(client):
    for path in ['/api/intake/run', '/api/encoding/detect', '/api/fields/normalize', '/api/content/normalize', '/api/reconcile']:
        response = client.post(path, json={})
        assert response.status_code == 200
    first = client.get("/api/runs").json()
    second = client.get("/api/runs").json()
    assert len(first["runs"]) == len(second["runs"]) == 1
    assert first == second

TWO_BOX = {
    "index_records": [{"archive_id": "000123", "box_id": "07"}, {"archive_id": "000123", "box_id": "08"}],
    "normalized_records": [
        {"source_line": 2, "archive_id": "000123", "box_id": "", "raw": {"档号": "000123", "盒号": ""}},
        {"source_line": 3, "archive_id": "000123", "box_id": "07"},
    ],
}

def test_reconcile_records_api(client):
    data = client.post("/api/reconcile", json=TWO_BOX).json()
    assert data["reason"] == "AMBIGUOUS"
    assert data["matched"] == [{"source_line": 3, "archive_id": "000123", "box_id": "07"}]
    assert data["doubtful"][0]["reason"] == "AMBIGUOUS_BOX"
    assert data["doubtful"][0]["candidates"] == ["07", "08"]
    assert data["doubtful"][0]["raw"] == {"档号": "000123", "盒号": ""}

def test_handover_flow_rerun_supplement_and_retrieve(client):
    recon = client.post("/api/reconcile", json=TWO_BOX).json()
    first = client.post("/api/export/evidence.csv", json={"reconcile": recon}).json()
    assert first["valid_count"] == 1 and first["doubtful_count"] == 1
    assert "AMBIGUOUS_BOX" in first["csv"] and "000123" in first["csv"]
    again = client.post("/api/export/evidence.csv", json={"reconcile": recon}).json()
    assert again["run_id"] == first["run_id"]
    runs = client.get("/api/runs").json()["runs"]
    assert len([r for r in runs if r["run_id"] == first["run_id"]]) == 1
    fetched = client.get(f"/api/runs/{first['run_id']}").json()
    assert fetched["result"]["csv"] == first["csv"]
    supplemented = dict(TWO_BOX, normalized_records=[
        {"source_line": 2, "archive_id": "000123", "box_id": "08"},
        {"source_line": 3, "archive_id": "000123", "box_id": "07"},
    ])
    recon2 = client.post("/api/reconcile", json=supplemented).json()
    assert recon2["reason"] == "OK"
    second = client.post("/api/export/evidence.csv", json={"reconcile": recon2}).json()
    assert second["run_id"] != first["run_id"]
    assert second["valid_count"] == 2 and second["doubtful_count"] == 0
    refetch = client.get(f"/api/runs/{first['run_id']}").json()
    assert refetch["result"]["csv"] == first["csv"]

def test_unknown_run_is_404(client):
    assert client.get("/api/runs/run-unknown").status_code == 404
