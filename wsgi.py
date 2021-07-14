from app import app

if __name__ == "__main__":
	# Quick test configuration. Please use proper Flask configuration options
	# in production settings, and use a separate file or environment variables
	# to manage the secret key!
	app.secret_key = 'super secret key'
	app.config['SESSION_TYPE'] = 'filesystem'

	app.debug = True
	app.run()