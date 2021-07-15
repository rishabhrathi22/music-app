from wtforms import Form, StringField, PasswordField, validators

class RegisterForm(Form):
	name = StringField('Name',[validators.Length(min=1, max=50)])
	email = StringField('Email',[validators.Length(min=6, max=50)])
	password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords do not match'), validators.Length(min=8)])
	confirm = PasswordField('Confirm Password')

class LoginForm(Form):
	email = StringField('Email',[validators.Length(min=6, max=50)])
	password = PasswordField('Password', [validators.DataRequired(), validators.Length(min=8)])

class UploadSongForm(Form):
	title = StringField('Title',[validators.Length(min=1, max=50)])
	artist = StringField('Artist',[validators.Length(min=1, max=50)])
	album = StringField('Album',[validators.Length(min=1, max=50)])