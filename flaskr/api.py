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
	cursor.execute('select serial_no, id from videos order by serial_no desc limit {start}, {count}'.format(start=(page - 1) * pieces_num, count=pieces_num))

	# TODO 取得できなかった場合の処理
	row = cursor.fetchall()
	cursor.close()

	return json.dumps(row, default=default)

@app.route('/my/contributors/', methods=['POST'])
def post_my_contributor():
	post_data = json.loads(request.data.decode(sys.stdin.encoding))
	contributor_id = post_data['id']

	# contributor_idの存在チェック
	if not is_exists_record('contributors', 'id = {0}'.format(contributor_id)):
		response = jsonify(post_data)
		response.status_code = 400
		return response

	# TODO OAuthを実装した後に修正する(ログインユーザのuser_idを使用するように)
	# 既に登録されていないかのチェック
	if is_exists_record('users_contributors', 'user_id = {0} and contributor_id = {1}'.format(1, contributor_id)):
		response = jsonify(post_data)
		response.status_code = 401
		return response

	ins_cursor = db_connector.cursor(buffered = True)
	ins_cursor.execute('insert into users_contributors (user_id, contributor_id) values ({0}, {1})'.format(1, contributor_id))

	db_connector.commit()
	ins_cursor.close()

	response = jsonify(post_data)
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

"""
レコードの存在チェック

@type target_tbl: str
@param target_tbl: 存在チェク対象のテーブル
@type target_tbl: str
@param target_tbl: 取得条件
@return 取得結果が1件以上の時=true, 0件以下の時=false
"""
def is_exists_record(target_tbl, where):
	cnt_cursor = db_connector.cursor(dictionary = True)
	cnt_cursor.execute('select count(*) as count from {table} where {where}'.format(table=target_tbl, where=where))

	cnt_row = cnt_cursor.fetchone()
	cnt_cursor.close()
	if cnt_row['count'] > 0:
		return True
	else:
		return False
