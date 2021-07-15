from flask import Flask, redirect, url_for, request, render_template, session
from passlib.hash import sha256_crypt
from functools import wraps
import sqlite3
import os

from forms import RegisterForm, LoginForm, UploadSongForm

# storing mp3 files
UPLOAD_FOLDER = 'static/songs'
ALLOWED_EXTENSIONS = {'mp3'}

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
# Upload folder for songs
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
	result = curr.execute("SELECT * FROM songs WHERE user=?", (session['id'],)).fetchall()
	conn.close()

	return render_template('dashboard.html', message = message, songs = result)


# Upload a new song
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
			try:
				conn = sqlite3.connect("database.db")
				curr = conn.cursor()
				try:
					last_id = curr.execute('select * from songs').fetchall()[-1][0]
				except:
					last_id = 0

				filename = str(last_id + 1) + "-" + title + '.mp3'
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

				curr.execute("INSERT into songs (title, artist, album, filename, user) values (?,?,?,?,?)", (title, artist, album, filename, session['id']))
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


# Play song
@app.route('/play/<songid>')
def play(songid):
	conn = sqlite3.connect("database.db")
	curr = conn.cursor()
	result = curr.execute("SELECT * FROM songs WHERE id=?", (songid, )).fetchone()
	conn.close()
	return render_template('playsong.html', name = result[1], artist = result[2], album = result[3], filename = result[4])


# Delete a song
@app.route('/delete/<songid>')
@is_logged_in
def delete(songid):
	conn = sqlite3.connect("database.db")
	curr = conn.cursor()
	result = curr.execute("SELECT * FROM songs WHERE id=? AND user=?", (songid, session['id'])).fetchone()

	if result == None:
		conn.close()
		return "<h1>You are not authorized to delete this song.</h1>"

	file = os.path.join(app.config['UPLOAD_FOLDER'], result[4])
	curr.execute("DELETE FROM songs WHERE id=?", (songid,))
	conn.commit()

	if os.path.exists(file):
		os.remove(file)

	conn.close()
	return redirect(url_for('allsongs', message = "delete"))


if __name__ == "__main__":
	# Quick test configuration. Please use proper Flask configuration options
	# in production settings, and use a separate file or environment variables
	# to manage the secret key!
	app.secret_key = 'super secret key'
	app.config['SESSION_TYPE'] = 'filesystem'

	app.debug = True
	app.run()