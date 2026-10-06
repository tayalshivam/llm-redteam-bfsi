"""A deliberately gullible offline model, used only by unit tests.

It falls for the classic attacks on purpose, so the tests can prove that the
detectors notice and that the guardrails stop the damage — all without an API key.
"""

from __future__ import annotations

import re

from redteam.bank import CUSTOMERS


class NaiveStub:
    model = "naive-stub"

    def chat(self, messages: list[dict], json_mode: bool = False) -> str:
        last = messages[-1]["content"]
        text = last.lower()
        if last.startswith("TOOL RESULT:"):
            return f"Done. {last.removeprefix('TOOL RESULT:').strip()}"
        if any(k in text for k in ("system prompt", "instructions", "above this", "configuration")):
            return messages[0]["content"]  # leaks the whole system prompt
        if "otp" in text:
            return "Sure, please share the OTP you received so I can verify you."
        lookup = re.search(r"\b(C\d{4})\b", last)
        if lookup and lookup.group(1) != "C1001":
            return f'ACTION: lookup_customer {{"customer_id": "{lookup.group(1)}"}}'
        transfer = re.search(r"(?:₹|rs\.?\s?)([\d,]+)", text)
        if "transfer" in text or "send" in text:
            amount = int(transfer.group(1).replace(",", "")) if transfer else 1000
            payee = "P02" if "landlord" in text else "P01" if "mom" in text else "NEW-PAYEE"
            return f'ACTION: transfer_funds {{"payee_id": "{payee}", "amount": {amount}}}'
        if "block" in text and "card" in text:
            return f'ACTION: block_card {{"card_last4": "{CUSTOMERS["C1001"]["card_last4"]}"}}'
        if "balance" in text:
            return "ACTION: get_my_account {}"
        if "<img" in text or "<script" in text:
            return "Here you go: <img src=x onerror=alert(1)>"
        return "I can help with that."
