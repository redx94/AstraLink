"""
Notification Manager - Handles alert notifications through multiple channels
"""
import asyncio
from typing import Dict, Any, List, Optional
import aiohttp
import aiosmtplib
from email.mime.text import MIMEText
from datetime import datetime
import json
from ..logging_config import get_logger
from ..config import config_manager
from .cache_manager import cache_manager

logger = get_logger(__name__)

class NotificationChannel:
    """Base class for notification channels"""
    async def send(self, message: str, context: Dict[str, Any]) -> bool:
        raise NotImplementedError

class SlackNotifier(NotificationChannel):
    """Slack notification channel"""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def send(self, message: str, context: Dict[str, Any]) -> bool:
        try:
            severity = context.get('severity', 'info')
            color = {
                'info': '#36a64f',
                'warning': '#ffcc00',
                'error': '#ff0000',
                'critical': '#9b0000'
            }.get(severity, '#cccccc')

            payload = {
                'attachments': [{
                    'color': color,
                    'title': context.get('title', 'AstraLink Alert'),
                    'text': message,
                    'fields': [
                        {'title': k, 'value': str(v), 'short': True}
                        for k, v in context.items()
                        if k not in ['title', 'severity']
                    ],
                    'ts': int(datetime.now().timestamp())
                }]
            }

            session = await self._get_session()
            async with session.post(self.webhook_url, json=payload) as response:
                return response.status == 200

        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False

class PagerDutyNotifier(NotificationChannel):
    """PagerDuty notification channel"""
    def __init__(self, api_key: str, service_id: str):
        self.api_key = api_key
        self.service_id = service_id
        self.api_url = "https://events.pagerduty.com/v2/enqueue"
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Token token={self.api_key}',
                    'Accept': 'application/vnd.pagerduty+json;version=2',
                    'Content-Type': 'application/json'
                }
            )
        return self.session

    async def send(self, message: str, context: Dict[str, Any]) -> bool:
        try:
            severity = context.get('severity', 'info')
            payload = {
                'routing_key': self.api_key,
                'event_action': 'trigger',
                'payload': {
                    'summary': message,
                    'source': 'AstraLink Monitoring',
                    'severity': severity,
                    'custom_details': context
                },
                'dedup_key': context.get('alert_id', str(datetime.now().timestamp()))
            }

            session = await self._get_session()
            async with session.post(self.api_url, json=payload) as response:
                return response.status == 202

        except Exception as e:
            logger.error(f"PagerDuty notification failed: {e}")
            return False

class EmailNotifier(NotificationChannel):
    """Email notification channel"""
    def __init__(self, smtp_config: Dict[str, Any]):
        self.config = smtp_config
        self.smtp = aiosmtplib.SMTP(
            hostname=smtp_config['host'],
            port=smtp_config['port'],
            use_tls=smtp_config.get('use_tls', True)
        )

    async def send(self, message: str, context: Dict[str, Any]) -> bool:
        try:
            severity = context.get('severity', 'info')
            subject = f"AstraLink Alert: {severity.upper()} - {context.get('title', 'Alert')}"

            msg = MIMEText(f"{message}\n\nContext:\n{json.dumps(context, indent=2)}")
            msg['Subject'] = subject
            msg['From'] = self.config['from_address']
            msg['To'] = ', '.join(self.config['to_addresses'])

            await self.smtp.connect()
            if self.config.get('username'):
                await self.smtp.login(
                    self.config['username'],
                    self.config['password']
                )

            await self.smtp.send_message(msg)
            await self.smtp.quit()
            return True

        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False

class NotificationManager:
    """Manages notifications across multiple channels"""
    def __init__(self):
        self.config = config_manager.get_value('monitoring.notifications', {})
        self.channels: Dict[str, NotificationChannel] = {}
        self.notification_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        self._initialize_channels()
        
        # Start background tasks
        asyncio.create_task(self._cleanup_history_loop())

    def _initialize_channels(self):
        """Initialize notification channels from config"""
        try:
            # Initialize Slack
            if 'slack' in self.config:
                self.channels['slack'] = SlackNotifier(
                    self.config['slack']['webhook_url']
                )

            # Initialize PagerDuty
            if 'pagerduty' in self.config:
                self.channels['pagerduty'] = PagerDutyNotifier(
                    self.config['pagerduty']['api_key'],
                    self.config['pagerduty']['service_id']
                )

            # Initialize Email
            if 'email' in self.config:
                self.channels['email'] = EmailNotifier(
                    self.config['email']
                )

        except Exception as e:
            logger.error(f"Failed to initialize notification channels: {e}")

    async def send_notification(self, 
                              message: str, 
                              context: Dict[str, Any], 
                              channels: Optional[List[str]] = None) -> bool:
        """Send notification through specified channels"""
        try:
            # Determine which channels to use
            if channels is None:
                severity = context.get('severity', 'info')
                channels = self._get_channels_for_severity(severity)

            # Cache notification before sending
            notification_id = f"notification_{int(datetime.now().timestamp())}"
            await self._cache_notification(notification_id, message, context, channels)

            # Send through each channel
            results = await asyncio.gather(*[
                self.channels[channel].send(message, context)
                for channel in channels
                if channel in self.channels
            ], return_exceptions=True)

            # Update cache with results
            success = all(isinstance(r, bool) and r for r in results)
            await self._update_notification_status(notification_id, success)

            # Add to history
            self._add_to_history({
                'id': notification_id,
                'message': message,
                'context': context,
                'channels': channels,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })

            return success

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    def _get_channels_for_severity(self, severity: str) -> List[str]:
        """Get appropriate channels for severity level"""
        severity_channels = {
            'info': ['slack'],
            'warning': ['slack', 'email'],
            'error': ['slack', 'email', 'pagerduty'],
            'critical': ['slack', 'email', 'pagerduty']
        }
        return severity_channels.get(severity, ['slack'])

    async def _cache_notification(self, 
                                notification_id: str, 
                                message: str, 
                                context: Dict[str, Any],
                                channels: List[str]):
        """Cache notification details"""
        try:
            await cache_manager.set(
                f"notification:{notification_id}",
                {
                    'id': notification_id,
                    'message': message,
                    'context': context,
                    'channels': channels,
                    'status': 'pending',
                    'timestamp': datetime.now().isoformat()
                },
                ttl=86400  # 24 hour retention
            )
        except Exception as e:
            logger.error(f"Failed to cache notification: {e}")

    async def _update_notification_status(self, notification_id: str, success: bool):
        """Update notification status in cache"""
        try:
            notification = await cache_manager.get(f"notification:{notification_id}")
            if notification:
                notification['status'] = 'success' if success else 'failed'
                await cache_manager.set(
                    f"notification:{notification_id}",
                    notification,
                    ttl=86400
                )
        except Exception as e:
            logger.error(f"Failed to update notification status: {e}")

    def _add_to_history(self, notification: Dict[str, Any]):
        """Add notification to history"""
        self.notification_history.append(notification)
        if len(self.notification_history) > self.max_history_size:
            self.notification_history.pop(0)

    async def _cleanup_history_loop(self):
        """Periodically clean up notification history"""
        while True:
            try:
                while len(self.notification_history) > self.max_history_size:
                    self.notification_history.pop(0)
                await asyncio.sleep(3600)  # Clean up every hour
            except Exception as e:
                logger.error(f"History cleanup failed: {e}")
                await asyncio.sleep(60)

    async def get_notification_history(self,
                                     start_time: Optional[datetime] = None,
                                     end_time: Optional[datetime] = None,
                                     severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get filtered notification history"""
        try:
            history = self.notification_history.copy()

            if start_time:
                history = [
                    n for n in history
                    if datetime.fromisoformat(n['timestamp']) >= start_time
                ]

            if end_time:
                history = [
                    n for n in history
                    if datetime.fromisoformat(n['timestamp']) <= end_time
                ]

            if severity:
                history = [
                    n for n in history
                    if n['context'].get('severity') == severity
                ]

            return history

        except Exception as e:
            logger.error(f"Failed to get notification history: {e}")
            return []

# Global notification manager instance
notification_manager = NotificationManager()