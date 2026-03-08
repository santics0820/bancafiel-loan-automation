"""
Test script — sends all 4 BancaFiel HTML email types to a test address.
Usage:
    cd /path/to/bancafiel-loan-automation
    python scripts/test_emails.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src', 'lambdas', 'notification-sender'))

import boto3
from handler import _html_received, _html_approved, _html_rejected, EMAIL_SUBJECTS

# ── Config ──────────────────────────────────────────────────────────────────
TO_EMAIL   = 'garciamontesfernando@gmail.com'
FROM_EMAIL = 'bancafiel.noreply@gmail.com'
REGION     = 'us-east-1'

TEST_NAME   = 'Fernando García'
TEST_AMOUNT = 30000.0
TEST_ID     = 'A1B2C3D4'

ses = boto3.client('ses', region_name=REGION)

# ── Analyst notification HTML (inline — mirrors approval-notifier) ──────────
def _html_analyst() -> str:
    return """<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background:#05070a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#05070a;padding:40px 16px;">
    <tr><td align="center">
      <table width="580" cellpadding="0" cellspacing="0" border="0" style="max-width:580px;width:100%;">
        <tr><td align="center" style="padding-bottom:28px;">
          <table cellpadding="0" cellspacing="0" border="0"><tr>
            <td valign="middle" style="padding-right:10px;">
              <div style="width:32px;height:32px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#f1f5f9 0%,#cbd5e1 35%,#64748b 65%,#334155 100%);box-shadow:0 4px 16px rgba(148,163,184,0.35);"></div>
            </td>
            <td valign="middle"><span style="font-size:22px;font-weight:800;letter-spacing:0.06em;color:#ffffff;">BANCAFIEL</span></td>
          </tr></table>
        </td></tr>
        <tr><td style="background:#0f1218;border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:40px;box-shadow:0 20px 60px rgba(0,0,0,0.6);">
          <div style="display:inline-block;background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.3);border-radius:100px;padding:6px 16px;margin-bottom:20px;">
            <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#fbbf24;">⚡ &nbsp;Requiere revisión</span>
          </div>
          <h1 style="margin:0 0 8px;font-size:24px;font-weight:800;color:#ffffff;">Nueva solicitud pendiente</h1>
          <p style="margin:0 0 28px;font-size:15px;color:#94a3b8;line-height:1.6;">Se recibió una nueva solicitud que requiere tu aprobación.</p>
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
              <table width="100%"><tr>
                <td style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">Cliente</td>
                <td align="right" style="font-size:14px;font-weight:700;color:#ffffff;">Fernando García</td>
              </tr></table>
            </td></tr>
            <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
              <table width="100%"><tr>
                <td style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">Monto solicitado</td>
                <td align="right" style="font-size:14px;font-weight:700;color:#ffffff;">$30,000 MXN</td>
              </tr></table>
            </td></tr>
            <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
              <table width="100%"><tr>
                <td style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">Riesgo de fraude</td>
                <td align="right" style="font-size:14px;font-weight:700;color:#6ee7b7;">BAJO (12)</td>
              </tr></table>
            </td></tr>
            <tr><td style="padding:8px 0;">
              <table width="100%"><tr>
                <td style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">Folio</td>
                <td align="right" style="font-size:14px;font-weight:700;color:#e2e8f0;">A1B2C3D4</td>
              </tr></table>
            </td></tr>
          </table>
          <div style="text-align:center;margin-top:32px;">
            <a href="https://bancafiel.com/dashboard" style="display:inline-block;background:linear-gradient(135deg,#e2e8f0 0%,#94a3b8 100%);color:#0f172a;font-size:14px;font-weight:800;letter-spacing:0.04em;text-decoration:none;padding:16px 40px;border-radius:14px;">
              Revisar solicitud →
            </a>
          </div>
        </td></tr>
        <tr><td align="center" style="padding-top:28px;">
          <p style="margin:0;font-size:12px;color:#475569;line-height:1.6;">
            BancaFiel — Sistema interno de crédito.<br/>
            <a href="mailto:soporte@bancafiel.com" style="color:#60a5fa;text-decoration:none;">soporte@bancafiel.com</a>
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ── Send all ─────────────────────────────────────────────────────────────────
EMAILS = [
    {
        'subject': EMAIL_SUBJECTS['received'],
        'html':    _html_received(TEST_NAME, TEST_AMOUNT, TEST_ID),
        'label':   'received',
    },
    {
        'subject': EMAIL_SUBJECTS['approved'],
        'html':    _html_approved(TEST_NAME, TEST_AMOUNT, TEST_ID),
        'label':   'approved',
    },
    {
        'subject': EMAIL_SUBJECTS['rejected'],
        'html':    _html_rejected(TEST_NAME, TEST_ID),
        'label':   'rejected',
    },
    {
        'subject': '[BancaFiel] Nueva solicitud — Fernando García (TEST)',
        'html':    _html_analyst(),
        'label':   'analyst-notifier',
    },
]

def main():
    print(f"\n📧  Sending {len(EMAILS)} test emails to {TO_EMAIL}\n")
    for e in EMAILS:
        try:
            ses.send_email(
                Source=FROM_EMAIL,
                Destination={'ToAddresses': [TO_EMAIL]},
                Message={
                    'Subject': {'Data': e['subject'], 'Charset': 'UTF-8'},
                    'Body':    {'Html': {'Data': e['html'], 'Charset': 'UTF-8'}},
                }
            )
            print(f"  ✅  {e['label']}")
        except Exception as err:
            print(f"  ❌  {e['label']} — {err}")
    print()

if __name__ == '__main__':
    main()
