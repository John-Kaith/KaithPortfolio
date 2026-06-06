from email.mime.text import MIMEText
from email.utils import formataddr
from flask import Flask, render_template, request, redirect, url_for
import logging
import os
import smtplib

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
logger = logging.getLogger(__name__)


def send_contact_email(name, email, message):
    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    smtp_to = os.environ.get('SMTP_TO', smtp_email)
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))

    if not smtp_email:
        logger.error('Contact email failed: SMTP_EMAIL is not set')
        return False
    if not smtp_password:
        logger.error('Contact email failed: SMTP_PASSWORD is not set')
        return False
    if not smtp_to:
        logger.error('Contact email failed: SMTP_TO is not set')
        return False

    subject = f'Portfolio message from {name}'
    body = (
        f'You received a new message from your portfolio contact form.\n\n'
        f'Name: {name}\n'
        f'Email: {email}\n\n'
        f'Message:\n{message}\n\n'
        f'---\n'
        f'Reply to this email to respond directly to {name}.'
    )

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = formataddr((f'{name} via Portfolio', smtp_email))
    msg['To'] = smtp_to
    msg['Reply-To'] = formataddr((name, email))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, [smtp_to], msg.as_string())

        logger.info('Contact email sent to %s', smtp_to)
        return True
    except Exception:
        logger.exception('SMTP send failed')
        return False


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
        if name and email and message:
            if send_contact_email(name, email, message):
                status = 'success'

        return redirect(url_for('contact', status=status))

    status = request.args.get('status')
    return render_template('contact.html', status=status)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
