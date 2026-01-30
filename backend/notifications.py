import os

class NotificationService:
    def __init__(self):
        # For now, notifications are disabled
        # We'll add Firebase later
        self.enabled = False
        print("Notifications disabled - will add Firebase later")
    
    async def send_alert(self, setup):
        """Send push notification for alert"""
        if not self.enabled:
            # Just print to console for now
            print(f"📱 NOTIFICATION: {setup['ticker']} {setup['direction']} - Score: {setup['score']}")
            return