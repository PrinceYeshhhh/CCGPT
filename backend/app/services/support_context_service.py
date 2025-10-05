"""
Service to provide generic customer support fallback context when no documents are available.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional

from app.core.config import settings


class SupportContextService:
    """Loads and serves generic customer support context content.

    The content is stored in a small static JSON file at app/data/default_support_context.json.
    """

    def __init__(self) -> None:
        self._cache: Optional[Dict[str, Any]] = None

    def _load_default_context(self) -> Dict[str, Any]:
        if self._cache is not None:
            return self._cache

        # Resolve path relative to backend/app/
        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_path = os.path.join(base_dir, "data", "default_support_context.json")

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
        except Exception:
            # Minimal inline fallback to ensure graceful behavior even if the file is missing
            self._cache = {
                "faqs": [
                    {
                        "q": "I can't log in.",
                        "a": "Please try resetting your password using the 'Forgot Password' link and ensure caps lock is off."
                    },
                    {
                        "q": "How can I track my order?",
                        "a": "You can track your order from your dashboard under 'My Orders'."
                    },
                    {
                        "q": "The product I received is defective.",
                        "a": "I'm sorry about that. Please share your order ID so we can assist with a replacement or refund."
                    }
                ],
                "guidelines": [
                    "Be polite, empathetic, and concise.",
                    "Offer next steps and links where appropriate.",
                    "Encourage contacting human support when needed."
                ]
            }

        return self._cache

    def get_generic_customer_service_context(self, workspace_id: Optional[str] = None) -> str:
        """Return a compact text block suitable as fallback context.

        Args:
            workspace_id: Optional workspace identifier (reserved for future customization).
        """
        data = self._load_default_context()
        lines: list[str] = []

        lines.append("Generic Customer Support FAQs and Guidelines:\n")
        for faq in data.get("faqs", [])[:6]:
            q = faq.get("q", "")
            a = faq.get("a", "")
            if q and a:
                lines.append(f"Q: {q}\nA: {a}\n")

        guidelines = data.get("guidelines", [])
        if guidelines:
            lines.append("Guidelines:")
            for g in guidelines[:6]:
                lines.append(f"- {g}")

        return "\n".join(lines)


support_context_service = SupportContextService()


