from flask import request, render_template, jsonify
from flaskr import app
from flaskr import db_connector
import urllib.request
import json
import xmltodict
import sys

@app.route('/videos/<int:videos_id>', methods=['GET'])
def get_video(videos_id):
	res = urllib.request.urlopen('http://ext.nicovideo.jp/api/getthumbinfo/sm' + str(videos_id))
	body = res.read()
	video_xml = xmltodict.parse(body)

	if 'nicovideo_thumb_response' in video_xml and 'thumb' in video_xml['nicovideo_thumb_response']:
		return json.dumps(video_xml['nicovideo_thumb_response']['thumb'], default=default)
	else:
		return '{}' # TODO 何を返すのがいいのか再考

@app.route('/videos/list/', methods=['GET'])
def get_videos_list():
	arg_page = request.args.get('page')
	pieces_num = 20
	page = 1

	if arg_page is not None and arg_page.isdigit() and int(arg_page) > 0:
		page = int(arg_page)

	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('select serial_no, id from videos order by serial_no desc limit %s, %s', [(page - 1) * pieces_num, pieces_num])

	# TODO 取得できなかった場合の処理
	row = cursor.fetchall()
	cursor.close()

	return json.dumps(row, default=default)

@app.route('/my/contributors/', methods=['POST'])
def post_my_contributor():
	# contributor_id = request.form['id']

	# # TODO OAuthを実装した後に修正する(ログインユーザのuser_idを使用するように)
	# contributor_idの存在チェック
	# sel_cursor = db_connector.cursor(dictionary = True)
	# sel_cursor.execute('select id from contributors where id = %s', [contributor_id])
	# # TODO 取得できなかった場合に処理を中断する実装
	# sel_cursor.fetchone()
	# sel_cursor.close()
	#
	# ins_cursor = db_connector.cursor(buffered = True)
	# ins_cursor.execute('insert into users_contributors (user_id, contributor_id) values (%s, %s)', [1, contributor_id])
	#
	# # TODO insertできなかった場合の処理
	# db_connector.commit()
	# ins_cursor.close()
	# print(request)

	post_data = request.data.decode(sys.stdin.encoding)

	response = jsonify(json.loads(post_data))
	response.status_code = 201

	return response

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
