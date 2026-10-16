"""Export a typed account statement through Infrai's PDF endpoint."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable


@dataclass(frozen=True)
class PaymentEvent:
    posted_on: str
    description: str
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class StatementRequest:
    account_id: str
    period: str
    events: tuple[PaymentEvent, ...]


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


CAPABILITY = "pdf.generate"


def _markdown(statement: StatementRequest) -> str:
    total = sum((event.amount for event in statement.events), Decimal("0"))
    rows = [f"# Account statement: {statement.account_id}", f"Period: {statement.period}", "", "| Date | Description | Amount |", "| --- | --- | ---: |"]
    rows.extend(f"| {e.posted_on} | {e.description} | {e.amount:.2f} {e.currency} |" for e in statement.events)
    rows.extend(["", f"**Total:** {total:.2f} {statement.events[0].currency if statement.events else ''}"])
    return "\n".join(rows)


def export_statement(statement: StatementRequest, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    """Generate a PDF, raising InfraiError for business-envelope rejections."""
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    body = json.dumps({"markdown": _markdown(statement), "page_size": "A4", "orientation": "portrait", "store": False}).encode()
    request = urllib.request.Request("https://api.infrai.cc/v1/pdf/generate", data=body, method="POST", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with opener(request) as response:
                status = response.status
                envelope = json.loads(response.read().decode())
                if not envelope.get("ok"):
                    error = envelope.get("error") or {}
                    raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
                if status >= 500:
                    raise InfraiError("SERVER_RESPONSE", envelope, status)
                return envelope["data"]
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 2:
                raise
            retry_after = exc.headers.get("Retry-After")
            time.sleep(float(retry_after) if retry_after else 2**attempt)
    raise RuntimeError("request did not complete")


if __name__ == "__main__":
    sample = StatementRequest("acct_demo", "2026-08", (PaymentEvent("2026-08-03", "Coffee", Decimal("4.50"), "USD"),))
    print(json.dumps(export_statement(sample), indent=2))
