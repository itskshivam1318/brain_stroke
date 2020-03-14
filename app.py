from flask import Flask, render_template, request, redirect, url_for, flash, session, logging
from flask_mysqldb import MySQL
import logging
import os
import pickle
from PIL import Image
import numpy as np
from matplotlib.pyplot import imshow
from sklearn.preprocessing import OneHotEncoder
import matplotlib.pyplot as plt
from os import path
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "flash message"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'stroke'

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/loginin', methods = ['GET','POST'])
def loginin():
    if request.method == "POST":
        email = request.form['email_id']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT password from users where email = %s",(email,))
        data = cur.fetchall()
        if data[0][0] == password :
            return redirect(url_for('home'))
        else :
            flash("Invalid Email_id or Password")
            return redirect(url_for('login'))
    return redirect(url_for('login'))



@app.route('/register')
def register():
    return render_template("register.html")


@app.route('/registration', methods=['POST'])
def registration():
    if request.method == "POST":
        flash("User registered Successfully.")
        fname = request.form['first_name']
        lname = request.form['last_name']
        email = request.form['email_id']
        password = request.form['password']
        gender = request.form['gender']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(fname,lname,email,password,gender) VALUES (%s,%s,%s,%s,%s)",
                    (fname, lname, email, password, gender))
        mysql.connection.commit()
        return redirect(url_for("register"))


@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        file = request.files['file']
        file.save(secure_filename(file.filename))
        print(file.filename)
        if path.exists("input.jpg"):
            os.remove("input.jpg")
        os.rename(file.filename, r'input.jpg')
        #shutil.move(file.filename,'/uploads')
        flash("File uploaded successfully")
    return redirect(url_for('output'))

@app.route('/about')
def about():
    return render_template("about.html")

def out():
    with open('model_pickle', 'rb') as f:
        mp = pickle.load(f)
    enc = OneHotEncoder()
    enc.fit([[0], [1]])
    def names(number):
        if (number == 0):
            return 'Stroke'
        else:
            return 'Normal'
    img = Image.open(r"input.jpg")
    x = np.array(img.resize((128, 128)))
    x = x.reshape(1, 128, 128, 3)
    answ = mp.predict_on_batch(x)
    classification = np.where(answ == np.amax(answ))[1][0]
    #imshow(img)
    return str(answ[0][classification] * 100) + '% Confidence This Is ' + names(classification)


@app.route('/output')
def output():
    return render_template('output.html', myfunction = out)

if __name__ == '__main__':
    app.run(debug=True)
