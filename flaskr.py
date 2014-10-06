from flask import Flask
import mysql.connector

# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# mysql configuration
DB_USER = 'testuser'
DB_PASSWORD = 'password'
DB_HOST = '127.0.0.1'
DB_NAME = 'go_lang_test'
DB_CHARSET = 'utf8'

# create application
app = Flask(__name__)
app.config.from_object(__name__)

db_connector = None

def connect_db():
	db_connector = mysql.connector.connect(
		user     = app.config['DB_USER'],
		password = app.config['DB_PASSWORD'],
		host     = app.config['DB_HOST'],
		database = app.config['DB_NAME'],
		charset  = app.config['DB_CHARSET'])

def get_db_connector():
	return db_connector

if __name__ == '__main__':
	connect_db()
	app.run()
