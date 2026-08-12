import io
import numpy as np
import pandas as pd


def login(client):
    return client.post("/auth/login", data={"email": "admin@test.local", "password": "TestPassword123!"}, follow_redirects=True)


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json["status"] == "ok"


def test_login_and_dashboard(client):
    r = login(client)
    assert r.status_code == 200
    assert b"Tableau de bord" in r.data


def test_demo_prediction(client):
    login(client)
    x = np.zeros((1000, 12), dtype=float)
    for i in range(12):
        x[:, i] = np.sin(np.linspace(0, 30, 1000) + i * 0.1)
    csv_bytes = pd.DataFrame(x, columns=["I","II","III","aVR","aVL","aVF","V1","V2","V3","V4","V5","V6"]).to_csv(index=False).encode()
    r = client.post("/analyze", data={"sampling_rate": "100", "ecg_file": (io.BytesIO(csv_bytes), "test.csv")}, content_type="multipart/form-data", follow_redirects=True)
    assert r.status_code == 200
    assert b"DEMO_SYNTHETIC" in r.data
