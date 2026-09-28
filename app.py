from collections import deque
from email.mime.text import MIMEText
from email.utils import formataddr
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import json
import logging
import mimetypes
import os
import re
import smtplib
import threading
import time
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()

# Configure logging at import time so INFO lines also reach Render's logs under gunicorn.
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')

# Python doesn't know .woff2 on every OS; register it so fonts get the right Content-Type.
mimetypes.add_type('font/woff2', '.woff2')

app = Flask(__name__)
logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10
HTTP_TIMEOUT_SECONDS = 15

# Drop the CV (any file name) into static/cv/ — the About page switches from
# "CV coming soon" to live View/Download buttons automatically.
CV_DIRECTORY = os.path.join(app.static_folder, 'cv')

# Skills on the About page: (name, logo file name without extension).
# A missing logo shows a dashed placeholder until a matching .svg/.png/.webp/.jpg
# file is added to static/images/logo/.
LOGO_DIRECTORY = os.path.join(app.static_folder, 'images', 'logo')
LOGO_EXTENSIONS = ('.svg', '.png', '.webp', '.jpg')
SKILL_GROUPS = [
    ('Technical & Design Stack', [
        ('Python', 'python'),
        ('Flask', 'flask'),
        ('PHP', 'php'),
        ('HTML', 'html'),
        ('CSS', 'css'),
        ('JavaScript', 'JavaScript'),
        ('C++', 'Cpp'),
        ('Figma', 'figma'),
        ('MySQL', 'mysql'),
        ('Supabase', 'supabase'),
        ('Git', 'Git'),
    ]),
    ('Video & Media Editing', [
        ('Adobe After Effects', 'AE'),
        ('Adobe Premiere Pro', 'premiere'),
        ('Adobe Media Encoder', 'mediaencoder'),
        ('Alight Motion', 'AM'),
        ('CapCut', 'capcut'),
        ('HandBrake', 'handbrake'),
    ]),
    ('AI & Productivity Tools', [
        ('Claude Code', 'claudecode'),
        ('Gemini', 'geminilogo'),
        ('ChatGPT', 'chatgpt'),
    ]),
]

# Portfolio projects, shown in this order. To add a website: put its screenshots in
# static/images/projects/ and add an entry below. The first screenshot is also the card
# image unless a smaller 'thumbnail' is given. 'url' and 'url_note' are optional;
# without a 'url' the popup shows "Not Available".
WEBSITE_PROJECTS = [
    {
        'id': 'learniqtrack',
        'name': 'LearnIQ Track',
        'summary': 'An AI-powered learning platform like Google Classroom, with a Bookworm-style '
                   'word game, leaderboards, and QR-code attendance.',
        'overview': 'LearnIQ Track is an AI-powered learning platform for schools, similar to Google '
                    'Classroom, with accounts for admins/principals, teachers, and students. With one '
                    'click, AI generates quizzes, activities, reviewers, and flashcards. Its main feature '
                    'is a Bookworm-style word game where students battle an AI rival, with leaderboards '
                    'to keep them competitive. Students scan QR codes to log attendance for their '
                    'subjects and work immersion, and there\'s a mobile app too.',
        'tech': ['Python', 'FastAPI', 'Supabase', 'Gemini 2.5 Flash', 'HTML', 'CSS', 'JavaScript',
                 'React Native', 'React 19', 'Expo SDK 54', 'Ubuntu Linux', 'Gmail SMTP'],
        'screenshots': ['learniqtrack-4.webp', 'learniqtrack-1.webp', 'learniqtrack-5.webp',
                        'learniqtrack-2.webp', 'learniqtrack-3.webp'],
        'thumbnail': 'learniqtrack-4-thumb.webp',
        'url': 'https://learniqtrack.site',
    },
    {
        'id': 'mediaverse',
        'name': 'MediaVerse',
        'summary': 'An e-commerce website where users can buy media, games, books, and educational '
                   'products with a simple, convenient shopping experience.',
        'overview': 'MediaVerse is an e-commerce website where users can buy media, games, books, and '
                    'educational products. It is designed to be easy to use, making browsing and '
                    'shopping simple and convenient.',
        'tech': ['Python', 'Flask', 'HTML', 'CSS', 'JavaScript', 'MySQL'],
        'screenshots': ['mediaverse-1.webp', 'mediaverse-2.webp', 'mediaverse-3.webp'],
        'thumbnail': 'mediaverse-1-thumb.webp',
        'url': 'https://mediaverse-968n.onrender.com',
        'url_note': 'Hosted on a free server, so it may take up to a minute to wake up.',
    },
    {
        'id': 'balaylanao',
        'name': 'Balaylanao',
        'summary': 'A booking website that helps customers explore accommodations and special offers '
                   'through a clear, user-friendly interface.',
        'overview': 'BalayLanao is a booking website designed to help customers easily explore '
                    'available accommodations and special offers. It provides clear information and a '
                    'user-friendly interface, making the booking process simple and convenient.',
        'tech': ['PHP', 'HTML', 'CSS', 'JavaScript', 'MySQL'],
        'screenshots': ['balaylanao-1.webp', 'balaylanao-2.webp', 'balaylanao-3.webp'],
        'thumbnail': 'balaylanao-1-thumb.webp',
    },
    {
        'id': 'ecoweave',
        'name': 'EcoWeave',
        'summary': 'An e-commerce website for handmade vases and artificial flowers, with shop, cart, '
                   'checkout, and cash-on-delivery orders.',
        'overview': 'EcoWeave is an e-commerce website for pink and white home accents, featuring '
                    'handmade vases and artificial flowers. Customers can browse the collection, manage '
                    'their cart, place orders, and pay cash on delivery.',
        'tech': ['PHP', 'HTML', 'CSS', 'JavaScript', 'MySQL'],
        'screenshots': ['ecoweave-1.webp', 'ecoweave-2.webp', 'ecoweave-3.webp'],
        'thumbnail': 'ecoweave-1-thumb.webp',
        'url': 'https://ecoweave-seven.vercel.app/',
    },
]

# Motion graphics: 'thumbnail' (in static/images/projects/) is also the video poster;
# 'video' is a file in static/videos/.
MOTION_PROJECTS = [
    {
        'id': 'maps',
        'name': 'Maps',
        'summary': 'Motion graphics edit for Google Maps.',
        'tools': ['After Effects', 'HandBrake'],
        'thumbnail': 'maps.webp',
        'video': 'Maps.mp4',
    },
    {
        'id': 'spotify',
        'name': 'Spotify',
        'summary': 'Motion graphics edit for Spotify.',
        'tools': ['Premiere Pro', 'After Effects'],
        'thumbnail': 'spotify.webp',
        'video': 'Spotify.mp4',
    },
]

MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254
MAX_MESSAGE_LENGTH = 5000
EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# Spam protection: cap contact emails per visitor and for the whole site.
RATE_LIMIT_WINDOW_SECONDS = 60 * 60
RATE_LIMIT_PER_VISITOR = 3
RATE_LIMIT_SITE_WIDE = 20

_rate_limit_lock = threading.Lock()
_visitor_sends = {}
_site_sends = deque()


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


def validate_contact_form(name, email, message):
    errors = {}

    if not name:
        errors['name'] = 'Please enter your name.'
    elif len(name) > MAX_NAME_LENGTH:
        errors['name'] = f'Please keep your name under {MAX_NAME_LENGTH} characters.'

    if not email:
        errors['email'] = 'Please enter your email.'
    elif len(email) > MAX_EMAIL_LENGTH or not EMAIL_PATTERN.match(email):
        errors['email'] = 'Please enter a valid email address.'

    if not message:
        errors['message'] = 'Please write a message.'
    elif len(message) > MAX_MESSAGE_LENGTH:
        errors['message'] = f'Please keep your message under {MAX_MESSAGE_LENGTH} characters.'

    return errors


def get_client_ip():
    # Render runs behind a proxy, so the visitor's address is the first X-Forwarded-For entry.
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    return forwarded_for.split(',')[0].strip() or request.remote_addr or 'unknown'


def allow_send(client_ip):
    now = time.monotonic()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    with _rate_limit_lock:
        while _site_sends and _site_sends[0] < cutoff:
            _site_sends.popleft()

        visitor_sends = [sent_at for sent_at in _visitor_sends.get(client_ip, []) if sent_at >= cutoff]
        _visitor_sends[client_ip] = visitor_sends

        if len(visitor_sends) >= RATE_LIMIT_PER_VISITOR or len(_site_sends) >= RATE_LIMIT_SITE_WIDE:
            return False

        visitor_sends.append(now)
        _site_sends.append(now)

        # Forget visitors whose window has passed so the table can't grow forever.
        if len(_visitor_sends) > 1000:
            for ip in [ip for ip, sends in _visitor_sends.items() if not sends or sends[-1] < cutoff]:
                del _visitor_sends[ip]

        return True


def _format_file_size(num_bytes):
    if num_bytes >= 1024 * 1024:
        return f'{num_bytes / (1024 * 1024):.1f} MB'
    return f'{max(1, round(num_bytes / 1024))} KB'


def find_logo(name):
    for extension in LOGO_EXTENSIONS:
        if os.path.isfile(os.path.join(LOGO_DIRECTORY, name + extension)):
            return f'images/logo/{name}{extension}'
    return None


def get_skill_groups():
    return [
        {'title': title, 'skills': [{'name': name, 'logo': find_logo(logo)} for name, logo in skills]}
        for title, skills in SKILL_GROUPS
    ]


def find_cv_filename():
    # With several PDFs, the last by name wins (e.g. YAMOMO_CV_2027.pdf over YAMOMO_CV_2026.pdf).
    try:
        pdfs = sorted(name for name in os.listdir(CV_DIRECTORY) if name.lower().endswith('.pdf'))
    except FileNotFoundError:
        return None
    return pdfs[-1] if pdfs else None


def get_cv_info():
    filename = find_cv_filename()
    if not filename:
        return None
    return {
        'filename': filename,
        'size': _format_file_size(os.path.getsize(os.path.join(CV_DIRECTORY, filename))),
    }


def send_cv(as_attachment):
    cv = get_cv_info()
    if not cv:
        return redirect(url_for('about'))

    response = send_from_directory(
        CV_DIRECTORY,
        cv['filename'],
        mimetype='application/pdf',
        as_attachment=as_attachment,
        download_name=cv['filename'],
    )
    # Keep the CV (phone number, email) out of search engine results.
    response.headers['X-Robots-Tag'] = 'noindex'
    return response


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html', cv=get_cv_info(), skill_groups=get_skill_groups())


@app.route('/cv')
def cv_view():
    return send_cv(as_attachment=False)


@app.route('/cv/download')
def cv_download():
    return send_cv(as_attachment=True)


@app.route('/portfolio')
def portfolio():
    return render_template(
        'portfolio.html',
        website_projects=WEBSITE_PROJECTS,
        motion_projects=MOTION_PROJECTS,
    )


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'GET':
        return render_template('contact.html', status=request.args.get('status'), form={}, errors={})

    form = {
        'name': request.form.get('name', '').strip(),
        'email': request.form.get('email', '').strip(),
        'message': request.form.get('message', '').strip(),
    }

    # Hidden "website" field: people never see it, bots fill it in. Pretend it worked.
    if request.form.get('website'):
        logger.warning('Contact form: spam trap triggered, message dropped')
        return redirect(url_for('contact', status='success'))

    errors = validate_contact_form(form['name'], form['email'], form['message'])
    if errors:
        return render_template('contact.html', status=None, form=form, errors=errors), 400

    if not allow_send(get_client_ip()):
        logger.warning('Contact form: rate limit reached')
        return render_template('contact.html', status='limited', form=form, errors={}), 429

    try:
        sent = send_contact_email(form['name'], form['email'], form['message'])
    except Exception:
        logger.exception('Contact form failed unexpectedly')
        sent = False

    if sent:
        return redirect(url_for('contact', status='success'))

    # Keep what they typed so they can try again without rewriting it.
    return render_template('contact.html', status='error', form=form, errors={}), 500


@app.route('/healthz')
def healthz():
    # Lightweight URL for an uptime monitor to ping so Render's free plan doesn't sleep.
    return 'ok'


if __name__ == '__main__':
    app.run(debug=True)
