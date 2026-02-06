from flask import Flask, render_template, request, redirect, url_for
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

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
            api_key = os.environ.get('SENDGRID_API_KEY')
            from_email = os.environ.get('SENDGRID_FROM')
            to_email = os.environ.get('SENDGRID_TO', from_email)

            if api_key and from_email and to_email:
                subject = f"New message from {name} via portfolio site"
                full_body = (
                    f"From: {name} <{email}>\n\n"
                    f"{message}"
                )

                mail = Mail(
                    from_email=from_email,
                    to_emails=to_email,
                    subject=subject,
                    plain_text_content=full_body,
                )

                try:
                    sg = SendGridAPIClient(api_key)
                    response = sg.send(mail)
                    if response.status_code in (200, 202):
                        status = 'success'
                    else:
                        status = 'error'
                except Exception:
                    status = 'error'

        return redirect(url_for('contact', status=status))

    status = request.args.get('status')
    return render_template('contact.html', status=status)

if __name__ == '__main__':
    app.run(debug=True)
