import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from .models import ServerEvent

class NotificationService:
    """Servicio de notificaciones"""
    
    @staticmethod
    def send_email(to_email, subject, body):
        """Enviar email"""
        try:
            smtp_host = os.environ.get('EMAIL_HOST')
            smtp_port = int(os.environ.get('EMAIL_PORT', '587'))
            smtp_user = os.environ.get('EMAIL_USER')
            smtp_password = os.environ.get('EMAIL_PASSWORD')
            from_email = os.environ.get('EMAIL_FROM', smtp_user)
            
            if not all([smtp_host, smtp_user, smtp_password]):
                return False
            
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    @staticmethod
    def send_webhook(url, data):
        """Enviar webhook"""
        try:
            webhook_secret = os.environ.get('WEBHOOK_SECRET')
            headers = {'Content-Type': 'application/json'}
            if webhook_secret:
                headers['X-Webhook-Secret'] = webhook_secret
            
            response = requests.post(url, json=data, headers=headers, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending webhook: {e}")
            return False
    
    @staticmethod
    def notify_event(server, event_type, message, player_name=None, metadata=None):
        """Notificar evento y guardar en base de datos"""
        # Guardar evento
        event = ServerEvent.objects.create(
            server=server,
            event_type=event_type,
            message=message,
            player_name=player_name,
            metadata=metadata or {}
        )
        
        # Enviar notificaciones según configuración
        webhook_url = os.environ.get('WEBHOOK_URL')
        if webhook_url:
            NotificationService.send_webhook(webhook_url, {
                'server': server.name,
                'event_type': event_type,
                'message': message,
                'player_name': player_name,
                'timestamp': event.created_at.isoformat()
            })
        
        # Email para eventos críticos
        critical_events = ['server_crash', 'backup_failed']
        if event_type in critical_events:
            admin_email = os.environ.get('ADMIN_EMAIL')
            if admin_email:
                NotificationService.send_email(
                    admin_email,
                    f"[{server.name}] {event_type}",
                    f"<h2>{server.name}</h2><p>{message}</p>"
                )
        
        return event


def send_notification(server, event_type, message, details=None):
    """
    Función helper para enviar notificaciones.
    Wrapper de NotificationService.notify_event para compatibilidad.
    """
    from django.utils import timezone
    
    # Si details es un dict, extraer metadata
    metadata = details if isinstance(details, dict) else {}
    
    # Crear evento en la base de datos
    try:
        event = ServerEvent.objects.create(
            server=server,
            event_type=event_type,
            message=message,
            details=metadata
        )
    except Exception as e:
        print(f"Error creating ServerEvent: {e}")
        event = None
    
    # Enviar notificaciones según configuración
    webhook_url = os.environ.get('WEBHOOK_URL')
    if webhook_url:
        NotificationService.send_webhook(webhook_url, {
            'server': server.name,
            'event_type': event_type,
            'message': message,
            'timestamp': timezone.now().isoformat() if event else None,
            **metadata
        })
    
    # Email para eventos críticos
    critical_events = ['server_crash', 'backup_failed', 'rcon_error']
    if event_type in critical_events:
        admin_email = os.environ.get('ADMIN_EMAIL')
        if admin_email:
            NotificationService.send_email(
                admin_email,
                f"[{server.name}] {event_type}",
                f"<h2>{server.name}</h2><p>{message}</p>"
            )
    
    return event

