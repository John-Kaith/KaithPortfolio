from flask import Flask, render_template, request, redirect, url_for
import os

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

        # For now, do not actually send an email in production.
        # If the user filled all fields, consider it a "successful" send
        # so the UI can show a confirmation modal.
        status = 'error'
        if name and email and message:
            status = 'success'

        return redirect(url_for('contact', status=status))

    status = request.args.get('status')
    return render_template('contact.html', status=status)

if __name__ == '__main__':
    app.run(debug=True)
