from flask import Flask, render_template, request, redirect, url_for
import os
import smtplib
import ssl

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

        if name and email and message:
            gmail_user = os.environ.get('GMAIL_USER')
            gmail_pass = os.environ.get('GMAIL_APP_PASSWORD')
            to_email = gmail_user  # send to your own inbox

            if gmail_user and gmail_pass:
                subject = f"New message from {name} via portfolio site"
                body = (
                    f"From: {name} <{email}>\n"
                    f"To: {to_email}\n"
                    f"Subject: {subject}\n\n"
                    f"{message}"
                )

                context = ssl.create_default_context()
                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                        server.login(gmail_user, gmail_pass)
                        server.sendmail(gmail_user, to_email, body)
                except Exception:
                    # For now just ignore errors and redirect back
                    pass

        return redirect(url_for('contact'))

    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)
