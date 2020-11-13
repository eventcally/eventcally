from project import app
from project.views.utils import track_analytics
from flask import url_for, render_template, request, redirect

@app.route("/")
def home():
    if 'src' in request.args:
        track_analytics("home", '', request.args['src'])
        return redirect(url_for('home'))

    return render_template('home.html')

@app.route("/example")
def example():
    return render_template('example.html')

@app.route("/impressum")
def impressum():
    return render_template('impressum.html')

@app.route("/datenschutz")
def datenschutz():
    return render_template('datenschutz.html')

@app.route("/developer")
def developer():
    return render_template('developer/read.html')