from flaskr import app
from flaskr import db_connector
import json

@app.route('/')
def hello_world():
	return 'Hello World!'

@app.route('/videos/<int:videos_id>', methods=['GET'])
def get_video(videos_id):
	cursor = db_connector.cursor(dictionary = True)
	cursor.execute("select * from videos where id = %s", [videos_id])

	# TODO 取得できなかった場合の処理
	row = cursor.fetchone()
	cursor.close()

	return json.dumps(row, default=default)

@app.route('/videos/list/', methods=['GET'])
def get_videos_list():
	cursor = db_connector.cursor(dictionary = True)
	cursor.execute("select * from videos limit 20")

	# TODO 取得できなかった場合の処理
	row = cursor.fetchall()
	cursor.close()

	return json.dumps(row, default=default)

def default(obj):
	import calendar, datetime

	if isinstance(obj, datetime.datetime):
		if obj.utcoffset() is not None:
			obj = obj - obj.utcoffset()
	millis = int(
		calendar.timegm(obj.timetuple()) * 1000 +
		obj.microsecond / 1000
	)
	return millis
