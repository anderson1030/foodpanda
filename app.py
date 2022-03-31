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
app.secret_key = 'foodpanda'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://admin:admin@localhost/foodpanda"
db = SQLAlchemy(app)

class User(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	is_super_user = db.Column(db.Boolean(),default=False)
	address = db.Column(db.String(520), unique=False, nullable=False)
	username = db.Column(db.String(80), unique=True, nullable=False)
	password = db.Column(db.String(150), unique=False, nullable=False)

class Food(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=False, nullable=False)
	price = db.Column(db.String(120), unique=False, nullable=False)
	product_detail = db.Column(db.Text(), unique=False, nullable=True)
	url_pic = db.Column(db.String(150), nullable=False)

class Order(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	food_id = db.Column(db.Integer, nullable=True)
	time = db.Column(db.String(80),nullable=False)
	user_id = db.Column(db.Integer,nullable=True)
	status = db.Column(db.String(40),nullable=False)
	
	
class RegisterForm(Form):

	username = StringField('Username', [validators.DataRequired(), validators.length(min=4, max=80)])
	address = StringField('Address', [validators.DataRequired(), validators.length(min=1, max=220)])
	password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords must match')])
	confirm = PasswordField('Confirm Password')

class LoginForm(Form):
	username = StringField('Username', [validators.DataRequired()])
	password = PasswordField('Password', [validators.DataRequired()])

#admin page 
class IndexView(AdminIndexView):
	def is_accessible(self):
		return (session["current_user"] and session['current_user']['superUser' ] )

	def inaccessible_callback(self,name,**kwarg):
		flash('please login as admin','danger')
		return redirect(url_for('login'))

class UserModelView(ModelView):

    column_list = [
        'id', 'is_super_user', 'username','address','password'
    ]

class ProductModelView(ModelView):

    column_list = [
        'id', 'name', 'price','url_pic'
    ]

class OrderModelView(ModelView):

    column_list = [
        'id', 'food_id', 'time','user_id','status'
    ]

admin = Admin(app,index_view=IndexView())
admin.add_view(UserModelView(User,db.session))
admin.add_view(ProductModelView(Food,db.session))
admin.add_view(OrderModelView(Order,db.session))



@app.route('/')
@app.route('/home')
def index():
	return render_template('home.html')

@app.route('/logout')
def logout():
	session.pop('current_user',None)

	return redirect(url_for('index'))

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/product')
def products():
	try:
		if session['current_user']:
			product = Food.query.all()
			return render_template('product.html' , product = product)
	except KeyError:
		flash('Please login first!','danger')
		return redirect(url_for('login'))

	return render_template('product.html')

@app.route('/myorder')
def myorder():
    try:
        if session['current_user']:
            user = User.query.filter_by(username=session['current_user']['username']).first()
            orders = Order.query.filter_by(user_id=user.id).all()
            foods = Food.query.all()
            return render_template('myorder.html',orders=orders,foods=foods,user=user)
    except KeyError:
        flash('please login','danger')
        return redirect(url_for('login'))

    return render_template('myorder.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		address = form.address.data
		username = form.username.data
		password = sha256_crypt.hash(str(form.password.data))

		#create cursor
		
		result = User.query.filter_by(username=username).first()
		if result:
			flash("The username is registered", 'danger')
		else:
			new_user = User(username=username,password=password,address=address)
			db.session.add(new_user)
			db.session.commit()
			flash("You are now registered", 'success')
			return redirect(url_for('index'))
	return render_template('register.html', form = form)





@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm(request.form)
	if request.method == 'POST' and form.validate():
		username = form.username.data
		password_candidate = form.password.data

		result = User.query.filter_by(username=username).first()  

		if result:
			password = result.password

			if sha256_crypt.verify(password_candidate, password):
				session['current_user'] = {
					"username":username,
					"superUser": result.is_super_user
					}


				flash("Login Success", 'success')
				return redirect(url_for('index'))

			else:
				flash("Password does not matched", 'danger')
		else:
			flash('NO USER', 'danger')
	return render_template('login.html', form = form)
	
@app.route('/order/<int:id>/')
def order(id):
	food = Food.query.filter_by(id=id).first()
	user = User.query.filter_by(username=session['current_user']['username']).first()
	time = str(datetime.now())
	new_order = Order(food_id=id,time=time,status='Preparing',user_id=user.id)
	db.session.add(new_order)
	db.session.commit()
	order = Order.query.filter_by(time=time).first()

	api_url = 'http://47.242.56.77:4000/order'

	create_row_data = {
		'id': order.id,
		'food':food.name,
		'time':time,
		'status':'Preparing',
		'customer':user.username,
		'address':user.address
	}
	r = requests.post(url=api_url, json=create_row_data)
	
	#dictToSend = {'question':'what is the answer?'}
	#res = requests.post('http://localhost:4000/order', json=dictToSend)
	#print ('response from server:'),res.text
	#dictFromServer = res.json()
	return render_template('result.html', address=user.address, food=food.name, time=time, id=order.id)



@app.route('/api/order', methods=['GET'])
def Api():
	orderlist = []

	orders = Order.query.all()
	for order in orders:
		food = Food.query.filter_by(id=order.food_id).first()
		user = User.query.filter_by(id=order.user_id).first()
		create_row_data = {
			'id': order.id,
			'food':food.name,
			'time':order.time,
			'status':order.status,
			'customer':user.username,
			'address':user.address
		}
		orderlist.append(create_row_data)
	return jsonify(orderlist)


#@app.route('/order')
def order():
	api_url = 'http://47.242.56.77:4000/order'
	address = "Address, Kowloon"
	food = "pizza"
	time = str(datetime.now())
	


	order.id = "1236"
	create_row_data = {
		'id': "1235",
		'food':"pizza",
		'time':time,
		'status':'prepare'
	}
	r = requests.post(url=api_url, json=create_row_data)
	
	#dictToSend = {'question':'what is the answer?'}
	#res = requests.post('http://localhost:4000/order', json=dictToSend)
	#print ('response from server:'),res.text
	#dictFromServer = res.json()
	return jsonify('', render_template('result.html', address=address, food=food, time=time, id=order.id))
@app.route('/compelete', methods=['POST'])
def complete():
	request_data = request.get_json(force=True)
	id = request_data['id']
	status = request_data['status']
	Order.query.filter_by(id=id).update({Order.status:status})
	db.session.commit()
	return redirect(url_for('index'))


@app.route('/updatedata', methods=['POST'])
def getdata():
    try:
        if session['current_user']:
            user = User.query.filter_by(username=session['current_user']['username']).first()
            orders = Order.query.filter_by(user_id=user.id).all()
            foods = Food.query.all()
            return jsonify('',render_template('myorderupdate.html',orders=orders,foods=foods,user=user))
    except KeyError:
        flash('please login','danger')
        return redirect(url_for('login'))






if __name__ == '__main__':
	# db.create_all()
	app.run(debug = True, port=5000, host='0.0.0.0')
