from tkinter import NONE
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, jsonify
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin,AdminIndexView
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from flask_admin.form.upload import ImageUploadField
import requests
import json

# Config SQL
app = Flask(__name__)
app.secret_key = 'Foodpanda'
app.config["SQLALCHEMY_DATABASE_URI"] = ""

class User(db.Model):

	id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=1, increment=1),primary_key=True)
	username = db.Column(db.String(80), unique=True, nullable=False)
	address = db.Column(db.String(520), unique=False, nullable=False)
	password = db.Column(db.String(150), unique=False, nullable=False)



class Product(db.Model):
	id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=1, increment=1), primary_key=True)
	name = db.Column(db.String(80), unique=False, nullable=False)
	price = db.Column(db.String(120), unique=False, nullable=False)
	url_pic = db.Column(db.String(150), nullable=False)



class Orders(db.Model):
    orderTime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=1, increment=1), primary_key=True)
    product_id = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer,nullable=True)
    product_name = db.Column(db.String(80))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Integer)

class RegisterForm(Form):
	username = StringField('Username', [validators.DataRequired(), validators.length(min=4, max=80)])
	address = StringField('Address', [validators.DataRequired(), validators.length(min=1, max=220)])
	password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords must match')])
	confirm = PasswordField('Confirm Password')

class LoginForm(Form):
	username = StringField('Username', [validators.DataRequired()])
	password = PasswordField('Password', [validators.DataRequired()])



@app.route('/')
@app.route('/home')
def index():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')


@app.route('/order', methods=['POST'])
def order():
	request_data = request.get_json()
	print(request_data)


	return 
	
@app.route('/send')
def send():
	api_url = 'http://localhost:4000/order'
	time = str(datetime.now())
	create_row_data = {
		'id': '1235',
		'time':time,
		'status':'preparing'
	}
	r = requests.post(url=api_url, json=create_row_data)
	
	return redirect(url_for('index'))





if __name__ == '__main__':
	#db.create_all()
	app.run(debug = True, port=5000)