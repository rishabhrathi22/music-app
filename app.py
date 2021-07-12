from flask import Flask, redirect, url_for, request, render_template, session, send_from_directory
from passlib.hash import sha256_crypt
from functools import wraps
import sqlite3
import os
from werkzeug.utils import secure_filename

from forms import RegisterForm, LoginForm, UploadSongForm

# storing mp3 files
UPLOAD_FOLDER = 'static/songs'
ALLOWED_EXTENSIONS = {'mp3'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Max size allowed = 6 MB
app.config['MAX_CONTENT_LENGTH'] = 6 * 1000 * 1000

# Home page
@app.route('/')
def index():
	return render_template('index.html')


""" Authentication Part """

# Register user
@app.route('/register', methods = ['GET', 'POST'])
def register():
	form = RegisterForm(request.form)

	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		password = sha256_crypt.encrypt(str(form.password.data))

		try:
			conn = sqlite3.connect("database.db")
			curr = conn.cursor()
			curr.execute("INSERT into users (name, email, password) values (?,?,?)",(name,email,password))
			conn.commit()
			conn.close()
			return render_template('register.html', form = form, success = True)

		except:
			conn.rollback()
			conn.close()
			return render_template('register.html', form = form, error = "Email already registered")

	return render_template('register.html', form = form)

# Login User
@app.route('/login', methods = ['GET', 'POST'])
def login():
	if 'logged_in' in session:
		return redirect(url_for("allsongs"))

	form = LoginForm(request.form)

	if request.method == 'POST' and form.validate():
		email = form.email.data
		ip_password = form.password.data

		conn = sqlite3.connect("database.db")
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
				return render_template('login.html', error = "Incorrect Password", form = form)

		else:
			return render_template('login.html', error = "Email not Registered", form = form)

		conn.close()

	return render_template('login.html', form = form)

# Check whether user is logged in
def is_logged_in(func):
	@wraps(func)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return func(*args,**kwargs)
		else:
			return redirect(url_for('login'))
	return wrap

# Logout user
@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('login'))

""" Songs functionality """

# View all Songs
@app.route('/songs')
@is_logged_in
def allsongs():
	message = request.args.get('message', '')

	conn = sqlite3.connect("database.db")
	curr = conn.cursor()
	curr.execute("SELECT * FROM songs")
	result = curr.fetchall()
	print(result)
	conn.commit()
	conn.close()

	return render_template('dashboard.html', message = message, songs = result)

	# cur=mysql.connection.cursor()

	# result=cur.execute("SELECT * from songs WHERE user_id = %s",[session['id']])

	# songs=cur.fetchall()

	# if result>0:
	# 	return render_template('dashboard.html',songs=songs)
	# else:
	# 	msg="NO PLAYLIST FOUND "

	# return render_template('dashboard.html',msg=msg)
	# cur.close()


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods = ['GET', 'POST'])
@is_logged_in
def upload():
	form = UploadSongForm(request.form)

	if request.method == 'POST' and form.validate():
		file = request.files['song']
		title = form.title.data
		artist = form.artist.data
		album = form.album.data

		# If the user does not select a file, the browser submits an empty file without a filename.
		if file.filename == '':
			return render_template('upload.html', error = "No file selected", form = form)

		if file and allowed_file(file.filename):
			filename = str(session['id']) + secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

			try:
				conn = sqlite3.connect("database.db")
				curr = conn.cursor()
				curr.execute("INSERT into songs (title, artist, album, url) values (?,?,?,?)",(title, artist, album, filename))
				conn.commit()
				conn.close()
				return redirect(url_for('allsongs', message = "upload"))

			except Exception as e:
				print(e)
				conn.rollback()
				conn.close()
				return render_template('upload.html', form = form, error = "Some error occurred")

			return redirect(url_for('allsongs', message = "upload"))

	return render_template('upload.html', form = form)


if __name__ == "__main__":
	# Quick test configuration. Please use proper Flask configuration options
	# in production settings, and use a separate file or environment variables
	# to manage the secret key!
	app.secret_key = 'super secret key'
	app.config['SESSION_TYPE'] = 'filesystem'

	app.debug = True
	app.run()