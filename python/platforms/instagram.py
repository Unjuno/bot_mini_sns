from __future__ import annotations
from .whatsapp import WhatsAppAdapter

class InstagramAdapter(WhatsAppAdapter):
    """Instagram Messaging uses the Meta Graph messaging shape; endpoint can be overridden."""
    def __init__(self, token=None, instagram_account_id=None, session=None):
        super().__init__(token=token or __import__("os").getenv("INSTAGRAM_ACCESS_TOKEN"), phone_number_id=instagram_account_id or __import__("os").getenv("INSTAGRAM_ACCOUNT_ID"), session=session)
        self.capabilities = __import__("platforms.catalog", fromlist=["PLATFORM_CATALOG"]).PLATFORM_CATALOG["instagram"]
    def parse_event(self, payload, headers=None):
        message = payload.get("message", payload)
        sender = payload.get("sender", {})
        return __import__("core.models", fromlist=["InboundEvent"]).InboundEvent(platform="instagram", user_id=str(sender.get("id") or payload.get("user_id")), content_type="text", text=message.get("text"))
    def send_reply(self, event, reply):
        for message in reply.messages:
            response = self.session.post(f"https://graph.facebook.com/v20.0/me/messages", headers={"Authorization": f"Bearer {self.token}"}, json={"recipient": {"id": event.user_id}, "message": {"text": message.text or message.media_url or ""}}, timeout=30); response.raise_for_status()
