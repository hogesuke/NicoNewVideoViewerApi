from flask import request, render_template, jsonify, make_response
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
	response = make_response()

	if 'nicovideo_thumb_response' in video_xml and 'thumb' in video_xml['nicovideo_thumb_response']:
		response.data = json.dumps(video_xml['nicovideo_thumb_response']['thumb'], default=default)
		response.status_code = 200
		return response
	else:
		# TODO 取得できなかった場合の表示について再考
		response.status_code = 204
		return response

@app.route('/videos/list/', methods=['GET'])
def get_videos_list():
	pieces_num = 20
	page = get_page_no(request.args.get('page'))

	# TODO OAuthを実装した後に修正する(ログインユーザのuser_idを使用するように)
	# TODO 未ログイン時の実装も別に必要
	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select vi.*, if(ucp.video_id <=> NULL, 'false', 'true') watched
		from videos vi
		left outer join users_completions ucp
		on vi.id = ucp.video_id and ucp.user_id = {user_id}
		order by serial_no desc
		limit {start}, {count}'''.format(user_id=1, start=(page - 1) * pieces_num, count=pieces_num))

	rows = cursor.fetchall()
	cursor.close()

	response = make_response()
	response.data = json.dumps(rows, default=default)
	response.status_code = 200
	return response

@app.route('/my/videos/list/', methods=['GET'])
def get_my_videos():
	piece_num = 20
	page = get_page_no(request.args.get('page'))

	# TODO OAuthを実装した後に修正する(ログインユーザのuser_idを使用するように)
	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select vi.*, if(ucp.video_id <=> NULL, 'false', 'true') watched
		from videos vi
		inner join videos_contributors vc
		on vi.id = vc.video_id
		inner join users_contributors uc
		on vc.contributor_id = uc.contributor_id
		left outer join users_completions ucp
		on vi.id = ucp.video_id and uc.user_id = ucp.user_id
		where uc.user_id = {user_id}
		order by vi.serial_no desc
		limit {start}, {count}'''.format(user_id=1, start=(page - 1) * piece_num, count=piece_num))

	rows = cursor.fetchall()
	cursor.close()

	response = make_response()
	response.data = json.dumps(rows, default=default)
	response.status_code = 200
	return response

@app.route('/my/contributors/', methods=['GET'])
def get_my_contributor():
	contributor_num = 20
	page = get_page_no(request.args.get('page'))

	# TODO OAuthを実装した後に修正する(ログインユーザのuser_idを使用するように)
	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select cb.*
		from users_contributors uc
		inner join contributors cb
		on uc.contributor_id = cb.id
		where uc.user_id = {user_id}
		order by uc.created_datetime desc
		limit {start}, {count}'''.format(user_id=1, start=(page - 1) * contributor_num, count=contributor_num))

	rows = cursor.fetchall()
	cursor.close()

	response = make_response()
	response.data = json.dumps(rows, default=default)
	response.status_code = 200
	return response

@app.route('/my/contributors/', methods=['POST'])
def post_my_contributor():
	post_data = json.loads(request.data.decode(sys.stdin.encoding))
	contributor_id = post_data['id']

	# TODO まだ登録されていないcontributorが指定された場合どうしよう…
	# contributor_idの存在チェック
	if not is_exists_record('contributors', 'id = {0}'.format(contributor_id)):
		response = jsonify(post_data)
		response.status_code = 400
		return response

	# TODO OAuthを実装した後に修正する(ログインユーザのuser_idを使用するように)
	# 既に登録されていないかのチェック
	if is_exists_record('users_contributors', 'user_id = {0} and contributor_id = {1}'.format(1, contributor_id)):
		response = jsonify(post_data)
		response.status_code = 400
		return response

	exec_sql('insert into users_contributors (user_id, contributor_id) values ({0}, {1})'.format(1, contributor_id), True)

	response = jsonify(post_data)
	response.status_code = 201

	return response

@app.route('/my/contributors/', methods=['DELETE'])
def delete_my_contributor():
	post_data = json.loads(request.data.decode(sys.stdin.encoding))
	contributor_id = post_data['id']

	# TODO まだ登録されていないcontributorが指定された場合どうしよう…
	# contributor_idの存在チェック
	if not is_exists_record('contributors', 'id = {0}'.format(contributor_id)):
		response = jsonify(post_data)
		response.status_code = 400
		return response

	# TODO OAuthを実装した後に修正する(ログインユーザのuser_idを使用するように)
	# 登録されているかのチェック
	if not is_exists_record('users_contributors', 'user_id = {0} and contributor_id = {1}'.format(1, contributor_id)):
		response = jsonify(post_data)
		response.status_code = 400
		return response

	exec_sql('delete from users_contributors where user_id = {0} and contributor_id = {1}'.format(1, contributor_id), True)

	response = jsonify(post_data)
	response.status_code = 201

	return response

@app.route('/videos/<int:video_id>/completion/', methods=['POST'])
def post_completion(video_id):

	# videoの存在チェック
	if not is_exists_record('videos', 'id = {0}'.format(video_id)):
		response = make_response()
		response.status_code = 400
		return response

	# completionの存在チェック
	if is_exists_record('completions', 'video_id = {0}'.format(video_id)):
		# TODO OAuthを実装した後に修正する(ログインユーザのuser_idを使用するように)
		# 既に視聴済み登録されていないかのチェック
		if is_exists_record('users_completions', 'user_id = {0} and video_id = {1}'.format(1, video_id)):
			response = make_response()
			response.status_code = 400
			return response
	else:
		exec_sql('insert into completions (video_id) values ({0})'.format(video_id), False)

	exec_sql('insert into users_completions (user_id, video_id) values ({0}, {1})'.format(1, video_id), True)

	response = make_response()
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
リクエストパラメータからページ番号を取得する

@type arg_page: str
@param arg_page: リクエストパラメータで指定されたpage
@return リクエストパラメータのpageに有効な値が設定されている場合は、
        リクエストパラメータのpageを数値に変換し返却。
        有効でない値の場合は、1を返却。
"""
def get_page_no(param_page):
	page = 1
	if param_page is not None and param_page.isdigit() and int(param_page) > 0:
		page = int(param_page)

	return page

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

"""
SQLの実行。
INSERT, UPDATE, DELETEのSQLを実行する。

@type sql: str
@param sql: 実行対象のsql
@type commit: bool
@param commit: commitするか否か
"""
def exec_sql(sql, commit):
	ins_cursor = db_connector.cursor()
	ins_cursor.execute(sql)
	ins_cursor.close()
	if commit:
		db_connector.commit()
