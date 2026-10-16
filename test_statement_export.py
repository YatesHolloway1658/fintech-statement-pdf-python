import json
from decimal import Decimal

from statement_export import PaymentEvent, StatementRequest, export_statement


class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return json.dumps({"ok": True, "data": {"job_id": "job_123"}}).encode()


def test_export_sends_statement_markdown_and_returns_data(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    seen = {}
    def opener(request):
        seen["method"] = request.method
        seen["body"] = json.loads(request.data)
        return Response()
    statement = StatementRequest("acct_7", "2026-08", (PaymentEvent("2026-08-01", "Payroll", Decimal("1200.00"), "USD"),))
    result = export_statement(statement, opener)
    assert result == {"job_id": "job_123"}
    assert seen["method"] == "POST"
    assert "Payroll" in seen["body"]["markdown"]
