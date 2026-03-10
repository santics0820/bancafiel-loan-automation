"""
POST /api/documents/verify
Synchronous INE OCR verification — called from frontend after photo capture.
Returns extracted fields so the user can confirm before submitting.
"""
import json
import boto3
import base64
import re
import os
import logging

logger = logging.getLogger(__name__)
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

CURP_RE = re.compile(r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9][0-9]$')
BEDROCK_MODEL = os.environ.get('BEDROCK_MODEL', 'us.anthropic.claude-sonnet-4-5-20250929-v1:0')

OCR_PROMPT = """Analyze this Mexican INE (Credencial para Votar) document image and extract the following fields.

Return ONLY a valid JSON object with these exact keys:
{
  "full_name": "APELLIDO PATERNO APELLIDO MATERNO NOMBRE(S) — exactly as printed",
  "curp": "18-character CURP code — exactly as printed, no spaces",
  "date_of_birth": "DD/MM/YYYY",
  "address": "full address as printed on the INE back",
  "expiry_date": "DD/MM/YYYY or null if not visible",
  "voter_key": "clave de elector or null"
}

Critical rules:
- CURP must be exactly 18 characters: 4 letters + 6 digits + H or M + 5 letters + 1 alphanumeric + 1 digit
- Copy every character exactly — do not correct or guess any character
- Return null for any field you cannot read clearly
- Return ONLY the JSON object, no explanations or markdown"""


def handler(event, context):
    try:
        body = json.loads(event.get('body') or '{}')
        image_b64 = body.get('image')

        if not image_b64:
            return _resp(400, {'error': 'Missing image field'})

        # Strip data URI prefix if present (e.g. "data:image/jpeg;base64,...")
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]

        image_bytes = base64.b64decode(image_b64)

        # Detect image format from magic bytes
        img_format = 'png' if image_bytes[:8] == b'\x89PNG\r\n\x1a\n' else 'jpeg'

        # Call Bedrock synchronously
        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL,
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'image': {
                            'format': img_format,
                            'source': {'bytes': image_bytes}
                        }
                    },
                    {'text': OCR_PROMPT}
                ]
            }]
        )

        raw = response['output']['message']['content'][0]['text'].strip()

        # Strip markdown code block if present
        if '```' in raw:
            parts = raw.split('```')
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith('json'):
                raw = raw[4:]

        fields = json.loads(raw.strip())

        curp = (fields.get('curp') or '').strip().upper().replace(' ', '')
        curp_valid = bool(CURP_RE.match(curp)) if curp else False

        warnings = []
        if not curp:
            warnings.append('No se detectó CURP — asegúrate de incluir el reverso de tu INE')
        elif not curp_valid:
            warnings.append('El CURP detectado no tiene el formato correcto — verifica que tu INE sea legible')

        return _resp(200, {
            'success': True,
            'fields': {
                'full_name':     fields.get('full_name'),
                'curp':          curp or None,
                'date_of_birth': fields.get('date_of_birth'),
                'address':       fields.get('address'),
                'expiry_date':   fields.get('expiry_date'),
                'voter_key':     fields.get('voter_key'),
            },
            'curp_valid': curp_valid,
            'warnings':   warnings,
        })

    except json.JSONDecodeError:
        logger.error('Bedrock returned non-JSON response')
        return _resp(422, {'error': 'No se pudo leer tu INE. Intenta con mejor iluminación y sin reflejos.'})
    except Exception as e:
        logger.error(f'verifyDocument error: {e}')
        return _resp(500, {'error': 'Error al procesar el documento. Intenta de nuevo.'})


def _resp(status, body):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body, ensure_ascii=False),
    }
