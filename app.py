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
import numpy as np
from tqdm import tqdm
import cv2
import os
import shutil
import itertools
import imutils
import matplotlib.pyplot as plt

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

@app.route('/existing')
def existing():
    cur =mysql.connection.cursor()
    cur.execute("SELECT * FROM cases")
    data = cur.fetchall()
    cur.close()
    return render_template("existing.html", case = data)

@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        file = request.files['file']
        file.save(secure_filename(file.filename))
        print(file.filename)
        source = file.filename
        dest = "/uploads"
        #shutil.move(source, dest)
        if path.exists("input.jpg"):
            os.remove("input.jpg")
        os.rename(file.filename, r'input.jpg')
        flash("File uploaded successfully")
    return redirect(url_for('output'))

@app.route('/upload')
def upload():
    return render_template("upload.html")

@app.route('/cases', methods = ['POST'])
def cases():
    if request.method == 'POST':
        flash("case registered Successfully.")
        fname = request.form['first_name']
        lname = request.form['last_name']
        email = request.form['email_id']
        age = request.form['age']
        gender = request.form['gender']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO cases(fname,lname,email,age,gender) VALUES (%s,%s,%s,%s,%s)",
                    (fname, lname, email, age, gender))
        mysql.connection.commit()
        return redirect(url_for('upload'))


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

def images():
    IMG_SIZE = (224, 224)
    img = cv2.imread('input.jpg')
    img = cv2.resize(img,dsize=IMG_SIZE,interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(gray, 45, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.erode(thresh, None, iterations=2)
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    c = max(cnts, key=cv2.contourArea)
    extLeft = tuple(c[c[:, :, 0].argmin()][0])
    extRight = tuple(c[c[:, :, 0].argmax()][0])
    extTop = tuple(c[c[:, :, 1].argmin()][0])
    extBot = tuple(c[c[:, :, 1].argmax()][0])
    img_cnt = cv2.drawContours(img.copy(), [c], -1, (0, 255, 255), 4)
    img_pnt = cv2.circle(img_cnt.copy(), extLeft, 8, (0, 0, 255), -1)
    img_pnt = cv2.circle(img_pnt, extRight, 8, (0, 255, 0), -1)
    img_pnt = cv2.circle(img_pnt, extTop, 8, (255, 0, 0), -1)
    img_pnt = cv2.circle(img_pnt, extBot, 8, (255, 255, 0), -1)
    ADD_PIXELS = 0
    new_img = img[extTop[1] - ADD_PIXELS:extBot[1] + ADD_PIXELS,
              extLeft[0] - ADD_PIXELS:extRight[0] + ADD_PIXELS].copy()
    plt.imshow(img)
    plt.xticks([])
    plt.yticks([])
    plt.title('Original image')
    plt.savefig('original.jpg')
    if path.exists("static/original.jpg"):
        os.remove("static/original.jpg")
    shutil.move('original.jpg', 'static/')
    plt.imshow(img_cnt)
    plt.xticks([])
    plt.yticks([])
    plt.title('Biggest contour')
    plt.savefig('contour.jpg')
    if path.exists("static/contour.jpg"):
        os.remove("static/contour.jpg")
    shutil.move('contour.jpg', 'static/')
    plt.imshow(img_pnt)
    plt.xticks([])
    plt.yticks([])
    plt.title('Extreme points')
    plt.savefig('points.jpg')
    if path.exists("static/points.jpg"):
        os.remove("static/points.jpg")
    shutil.move('points.jpg', 'static/')
    plt.imshow(new_img)
    plt.xticks([])
    plt.yticks([])
    plt.title('Brain image')
    plt.savefig('brain.jpg')
    if path.exists("static/brain.jpg"):
        os.remove("static/brain.jpg")
    shutil.move('brain.jpg', 'static/')


@app.route('/output')
def output():
    images()
    return render_template('output.html', myfunction = out, original = 'original.png')

if __name__ == '__main__':
    app.run(debug=True)
