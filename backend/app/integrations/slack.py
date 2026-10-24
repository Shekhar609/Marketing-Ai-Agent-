"""
Slack Connector for Real-Time Alerts, Approval Requests, and Executive Summaries
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import httpx
import logging

from app.integrations.base import BaseConnector

logger = logging.getLogger(__name__)


class SlackConnector(BaseConnector):
    """
    Slack Integration for posting real-time marketing notifications,
    critical revenue alerts, and interactive human-in-the-loop approval triggers.
    """

    @property
    def provider_name(self) -> str:
        return "slack"

    async def test_connection(self) -> Dict[str, Any]:
        webhook_url = self.credentials.get("webhook_url")
        bot_token = self.credentials.get("bot_token")
        target_channel = self.settings.get("default_channel", "#growth-alerts")
        
        if not webhook_url and not bot_token:
            return {"success": False, "message": "Slack webhook_url or bot_token is required"}

        if (webhook_url and "mock" in webhook_url) or (bot_token and "mock" in bot_token) or (bot_token == "test_token"):
            return {
                "success": True,
                "message": "Connected to Slack workspace (Sandbox / Mock Mode)",
                "channel": target_channel,
            }

        # Test real Incoming Webhook
        if webhook_url:
            if not webhook_url.startswith("http"):
                return {"success": False, "message": "Invalid Slack webhook URL format. Must start with http:// or https://"}
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    test_payload = {
                        "text": "⚡ *AIPNT Revenue Operations Platform:* Slack connection verified and active for real-time executive alerts."
                    }
                    res = await client.post(webhook_url, json=test_payload)
                    if res.status_code == 200 and res.text == "ok":
                        return {
                            "success": True,
                            "message": "Connected to Slack webhook successfully! Test notification delivered.",
                            "channel": target_channel,
                        }
                    return {"success": False, "status_code": res.status_code, "message": f"Slack webhook returned: {res.text}"}
            except Exception as exc:
                return {"success": False, "message": f"Slack webhook connection error: {str(exc)}"}
        
        # Test real Bot Token via auth.test
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {bot_token}"}
                )
                data = res.json()
                if data.get("ok"):
                    return {
                        "success": True,
                        "message": "Connected to Slack workspace successfully via Bot Token",
                        "team": data.get("team"),
                        "user": data.get("user"),
                        "channel": target_channel,
                    }
                return {"success": False, "message": data.get("error", "Slack auth failed")}
        except Exception as exc:
            return {"success": False, "message": f"Slack connection error: {str(exc)}"}

    async def sync(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Slack connector does not maintain inbound batch data, returns channel status.
        """
        return {
            "success": True,
            "provider": self.provider_name,
            "channel": self.settings.get("default_channel", "#growth-alerts"),
            "status": "READY",
        }

    async def send_message(
        self,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post message to Slack channel or webhook.
        """
        webhook_url = self.credentials.get("webhook_url")
        bot_token = self.credentials.get("bot_token")
        target_channel = channel or self.settings.get("default_channel", "#growth-alerts")

        # Mock handling
        if not webhook_url and not bot_token:
            return {"success": False, "message": "No Slack credentials configured"}
        
        if (webhook_url and "mock" in webhook_url) or (bot_token and "mock" in bot_token) or not webhook_url.startswith("http"):
            return {
                "success": True,
                "channel": target_channel,
                "text": text,
                "status": "DELIVERED_MOCK",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if webhook_url:
                    payload: Dict[str, Any] = {"text": text}
                    if blocks:
                        payload["blocks"] = blocks
                    res = await client.post(webhook_url, json=payload)
                    return {"success": res.status_code == 200, "status_code": res.status_code}
                else:
                    payload = {"channel": target_channel, "text": text}
                    if blocks:
                        payload["blocks"] = blocks
                    res = await client.post(
                        "https://slack.com/api/chat.postMessage",
                        json=payload,
                        headers={"Authorization": f"Bearer {bot_token}"}
                    )
                    return res.json()
        except Exception as exc:
            logger.error(f"Slack post failed: {exc}")
            return {"success": False, "error": str(exc)}

    async def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "INFO",
        action_url: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send formatted alert card to Slack.
        """
        icon = "🚨" if severity in ["HIGH", "CRITICAL"] else "ℹ️"
        text = f"{icon} *[{severity}] {title}*\n{message}"
        if action_url:
            text += f"\n👉 <{action_url}|View in Dashboard>"
        return await self.send_message(text=text, channel=channel)

    async def send_approval_request(
        self,
        request_id: int,
        title: str,
        reason: str,
        risk_level: str,
        approve_url: str,
        reject_url: str
    ) -> Dict[str, Any]:
        """
        Send Human-In-The-Loop approval notification with action links.
        """
        text = (
            f"⚠️ *Human Approval Required [Risk: {risk_level}]*\n"
            f"*Action:* {title}\n"
            f"*Reason:* {reason}\n"
            f"• <{approve_url}|Approve Action>\n"
            f"• <{reject_url}|Reject Action>"
        )
        return await self.send_message(text=text)
