from flask import Flask, redirect, url_for, request, render_template, session
from passlib.hash import sha256_crypt
from functools import wraps
import sqlite3

from forms import RegisterForm

user = []
app = Flask(__name__)
con = sqlite3.connect("employee.db")

@app.route('/')
def index():
	return render_template('index.html')


@app.route('/register', methods = ['GET', 'POST'])
def register():
	form = RegisterForm(request.form)

	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		password = sha256_crypt.encrypt(str(form.password.data))

		try: 
			conn = sqlite3.connect("users.db")
			curr = conn.cursor()
			curr.execute("INSERT into users (name, email, password) values (?,?,?)",(name,email,password))
			conn.commit()
			conn.close()
			return render_template('register.html', form = form, success = True)

		except:
			conn.rollback()
			conn.close()
			return render_template('register.html', form = form, error = "Email already registered")

	return render_template('register.html', form=form)


@app.route('/login', methods = ['GET', 'POST'])
def login():
	if 'logged_in' in session:
		return redirect(url_for("allsongs"))

	if request.method == 'POST':
		email = request.form['email']
		ip_password = request.form['password']

		conn = sqlite3.connect("users.db")
		curr = conn.cursor()
		result = curr.execute("SELECT * FROM users WHERE email = ?", (email, ))
		
		if data := result.fetchone():
			password = data[3]

			if sha256_crypt.verify(ip_password, password):
				session['logged_in'] = True
				session['id'] = data[0]
				session['name'] = data[1]
				return redirect(url_for('allsongs'))
			else:
				return render_template('login.html', error = "Incorrect Password")	

		else:
			return render_template('login.html', error = "Email not Registered")

		conn.close()

	return render_template('login.html')


def is_logged_in(func):
	@wraps(func)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return func(*args,**kwargs)
		else:
			return redirect(url_for('login'))
	return wrap


@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('login'))


@app.route('/songs')
@is_logged_in
def allsongs():
	return render_template('dashboard.html')

	# cur=mysql.connection.cursor()

	# result=cur.execute("SELECT * from songs WHERE user_id = %s",[session['id']])

	# songs=cur.fetchall()

	# if result>0:
	# 	return render_template('dashboard.html',songs=songs)
	# else:
	# 	msg="NO PLAYLIST FOUND "

	# return render_template('dashboard.html',msg=msg)
	# cur.close()


if __name__ == "__main__":
	# Quick test configuration. Please use proper Flask configuration options
	# in production settings, and use a separate file or environment variables
	# to manage the secret key!
	app.secret_key = 'super secret key'
	app.config['SESSION_TYPE'] = 'filesystem'

	app.debug = True
	app.run()