from fastapi.testclient import TestClient

from app.main import app


def test_ticket_confirmation_endpoint():
    with TestClient(app) as client:
        headers={"Authorization":"Bearer demo-cust_demo"}
        response=client.post("/api/chat",headers=headers,json={"message":"أريد تقديم شكوى","session_id":"test-session"})
        assert response.status_code == 200 and response.json()["requires_confirmation"]
        confirmed=client.post("/api/confirm",headers=headers,json={"session_id":"test-session","confirmed":True})
        assert confirmed.status_code == 200 and "تم إنشاء" in confirmed.json()["text"]

def test_api_denies_missing_identity():
    with TestClient(app) as client:
        assert client.post("/api/chat",json={"message":"باقتي","session_id":"x12"}).status_code == 401
