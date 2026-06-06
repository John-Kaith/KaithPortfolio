from email.mime.text import MIMEText
from email.utils import formataddr
from flask import Flask, render_template, request, redirect, url_for
import json
import logging
import os
import smtplib
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10
HTTP_TIMEOUT_SECONDS = 15


def _build_contact_message(name, email, message):
    subject = f'Portfolio message from {name}'
    body = (
        f'You received a new message from your portfolio contact form.\n\n'
        f'Name: {name}\n'
        f'Email: {email}\n\n'
        f'Message:\n{message}\n\n'
        f'---\n'
        f'Reply to this email to respond directly to {name}.'
    )
    return subject, body


def send_via_resend(name, email, message):
    api_key = os.environ.get('RESEND_API_KEY')
    to_email = os.environ.get('RESEND_TO') or os.environ.get('SMTP_TO')
    from_email = os.environ.get(
        'RESEND_FROM',
        'Portfolio Contact <onboarding@resend.dev>',
    )

    if not api_key:
        logger.error('Contact email failed: RESEND_API_KEY is not set')
        return False
    if not to_email:
        logger.error('Contact email failed: RESEND_TO or SMTP_TO is not set')
        return False

    subject, body = _build_contact_message(name, email, message)
    payload = json.dumps({
        'from': from_email,
        'to': [to_email],
        'subject': subject,
        'text': body,
        'reply_to': email,
    }).encode('utf-8')

    request_obj = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(request_obj, timeout=HTTP_TIMEOUT_SECONDS) as response:
            if 200 <= response.status < 300:
                logger.info('Contact email sent via Resend to %s', to_email)
                return True
            logger.error('Resend returned status %s', response.status)
            return False
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='replace')
        logger.error('Resend API error %s: %s', exc.code, error_body)
        return False
    except Exception:
        logger.exception('Resend send failed')
        return False


def send_via_smtp(name, email, message):
    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    smtp_to = os.environ.get('SMTP_TO', smtp_email)
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port_raw = os.environ.get('SMTP_PORT', '587')

    if not smtp_email:
        logger.error('Contact email failed: SMTP_EMAIL is not set')
        return False
    if not smtp_password:
        logger.error('Contact email failed: SMTP_PASSWORD is not set')
        return False
    if not smtp_to:
        logger.error('Contact email failed: SMTP_TO is not set')
        return False

    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        logger.error('Contact email failed: SMTP_PORT must be a number')
        return False

    subject, body = _build_contact_message(name, email, message)

    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = formataddr((f'{name} via Portfolio', smtp_email))
        msg['To'] = smtp_to
        msg['Reply-To'] = formataddr((name, email))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=SMTP_TIMEOUT_SECONDS) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, [smtp_to], msg.as_string())

        logger.info('Contact email sent via SMTP to %s', smtp_to)
        return True
    except Exception:
        logger.exception('SMTP send failed')
        return False


def send_contact_email(name, email, message):
    provider = os.environ.get('EMAIL_PROVIDER', 'auto').strip().lower()

    if provider == 'resend':
        return send_via_resend(name, email, message)
    if provider == 'smtp':
        return send_via_smtp(name, email, message)

    if os.environ.get('RESEND_API_KEY'):
        return send_via_resend(name, email, message)

    return send_via_smtp(name, email, message)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        status = 'error'
        try:
            if name and email and message:
                if send_contact_email(name, email, message):
                    status = 'success'
        except Exception:
            logger.exception('Contact form failed unexpectedly')
            status = 'error'

        return redirect(url_for('contact', status=status))

    status = request.args.get('status')
    return render_template('contact.html', status=status)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
