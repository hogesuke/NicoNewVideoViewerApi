from flask import request, render_template
from flaskr import app
from flaskr import db_connector
import urllib.request
import json
import xmltodict

@app.route('/videos/<int:videos_id>', methods=['GET'])
def get_video(videos_id):
	res = urllib.request.urlopen('http://ext.nicovideo.jp/api/getthumbinfo/sm' + str(videos_id))
	body = res.read()
	video_xml = xmltodict.parse(body)

	return json.dumps(video_xml, default=default)

@app.route('/videos/list/', methods=['GET'])
def get_videos_list():
	arg_page = request.args.get('page')
	pieces_num = 20
	page = 1

	if arg_page is not None and arg_page.isdigit() and int(arg_page) > 0:
		page = int(arg_page)

	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('select id from videos order by serial_no desc limit %s, %s', [(page - 1) * pieces_num, pieces_num])

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
