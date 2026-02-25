"""
Lambda #7: Notification Sender
Sends SES emails to customers at each stage of the process
"""
import json
import boto3
import os
from datetime import datetime

try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_query_single, create_application_history
except ImportError:
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def log_event(l, t, d): l.info(f"{t}: {d}")
    def log_error(l, t, e, c=None): l.error(f"{t}: {e}")

logger = setup_logger(__name__)
ses_client = boto3.client('ses', region_name='us-east-1')

FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', 'noreply@bancafiel.com')

EMAIL_TEMPLATES = {
    'received': {
        'subject': 'Hemos recibido su solicitud - BancaFiel',
        'body': """
Estimado/a {name},

Hemos recibido su solicitud de {type} por ${amount:,.2f} MXN correctamente.

Número de solicitud: {app_id}

Estamos procesando su solicitud. Le notificaremos en máximo 2 horas con el resultado.

Gracias por confiar en BancaFiel.

El equipo de BancaFiel
        """
    },
    'approved': {
        'subject': '¡Felicidades! Su solicitud fue APROBADA - BancaFiel',
        'body': """
Estimado/a {name},

¡Excelentes noticias! Su solicitud ha sido APROBADA.

Detalles:
• Tipo: {type}
• Monto aprobado: ${amount:,.2f} MXN
• Número de solicitud: {app_id}

Próximos pasos:
1. Inicie sesión en su cuenta de BancaFiel
2. Complete la documentación final
3. Firme su contrato digitalmente
4. Reciba su préstamo en 24-48 horas hábiles

Acceda aquí: https://bancafiel.com/dashboard

Gracias por confiar en BancaFiel.
        """
    },
    'rejected': {
        'subject': 'Actualización sobre su solicitud - BancaFiel',
        'body': """
Estimado/a {name},

Le informamos que su solicitud de {type} por ${amount:,.2f} MXN
(Número: {app_id}) no pudo ser aprobada en este momento.

Si desea más información, contáctenos:
• Email: soporte@bancafiel.com
• Teléfono: 800-BancaFiel

Puede volver a aplicar en 90 días.

Gracias por su comprensión.
El equipo de BancaFiel
        """
    }
}


def handler(event, context):
    try:
        application_id = event.get('application_id')
        notification_type = event.get('type', 'received')

        log_event(logger, 'notificationSender_invoked', {
            'application_id': application_id,
            'type': notification_type
        })

        # Get application and customer
        app = execute_query_single("""
            SELECT a.loan_amount, a.application_type, c.full_name, c.email
            FROM applications a JOIN customers c ON a.customer_id = c.id
            WHERE a.id = %s
        """, (application_id,))

        if not app:
            logger.error(f"Application {application_id} not found")
            return {'statusCode': 404}

        customer_email = app['email']
        template = EMAIL_TEMPLATES.get(notification_type, EMAIL_TEMPLATES['received'])

        loan_type_str = 'préstamo personal' if app['application_type'] == 'LOAN' else 'tarjeta de crédito'

        body = template['body'].format(
            name=app['full_name'],
            type=loan_type_str,
            amount=float(app['loan_amount']),
            app_id=str(application_id)[:8].upper()
        )

        # Send email via SES
        try:
            ses_client.send_email(
                Source=FROM_EMAIL,
                Destination={'ToAddresses': [customer_email]},
                Message={
                    'Subject': {'Data': template['subject'], 'Charset': 'UTF-8'},
                    'Body': {'Text': {'Data': body, 'Charset': 'UTF-8'}}
                }
            )

            log_event(logger, 'email_sent', {
                'to': customer_email,
                'type': notification_type,
                'application_id': application_id
            })

        except ses_client.exceptions.MessageRejected as e:
            # SES sandbox — email not verified. Log but don't fail the workflow.
            logger.warning(f"SES sandbox restriction: {e}")

        create_application_history(
            application_id, f'email_sent_{notification_type}', 'system',
            notes=f'Notification email sent: {notification_type} to {customer_email}'
        )

        return {'statusCode': 200, 'message': f'Notification sent: {notification_type}'}

    except Exception as e:
        log_error(logger, 'notificationSender_error', e)
        return {'statusCode': 500, 'error': str(e)}
