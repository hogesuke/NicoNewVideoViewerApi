from flask import request, session, render_template, jsonify, make_response, redirect
from flaskr import app
from flaskr import db_connector
from flaskr import twitter
import urllib.request
import json
import xmltodict
import sys

@app.route('/authorize/status/', methods=['GET'])
def get_authorize_status():
	response = make_response()

	if 'user_id' in session:
		response.status_code = 200
	else:
		response.status_code = 401

	return response

@app.route('/authorize/', methods=['GET'])
def get_authorize_url():
	request_token, request_token_secret = twitter.get_request_token()
	authorize_url = twitter.get_authorize_url(request_token)

	session['request_token'] = request_token
	session['request_token_secret'] = request_token_secret

	response = make_response()
	response.data = json.dumps({'authorize_url': authorize_url}, default=default)
	response.status_code = 200
	return response

@app.route('/callback/twitter/', methods=['GET'])
def callback_twitter():
	oauth_verifier = request.args['oauth_verifier']

	auth_session = twitter.get_auth_session(session['request_token'],
							 session['request_token_secret'],
							 method = 'POST',
							 data = {'oauth_verifier': oauth_verifier})
	verify = auth_session.get('account/verify_credentials.json')
	if verify.status_code != 200:
		response = make_response()
		response.status_code = 401
		return response
	user_info = verify.json()

	if not is_exists_record('users', 'provider_id = {0}'.format(user_info['id'])):
		exec_sql('insert into users(provider_id, provider_name, raw_name, name) values ({0}, \'{1}\', \'{2}\', \'{3}\')'.format(
			user_info['id'], 'twitter', user_info['screen_name'], user_info['name']), True)

	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select *
		from users
		where provider_id = {provider_id}'''.format(provider_id = user_info['id']))

	row = cursor.fetchone()
	cursor.close()

	session['user_id'] = row['id']
	return redirect('/')

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
	page = get_page_no(request.args.get('page'))
	perpage = get_perpage_no(request.args.get('perpage'))

	if 'user_id' in session:
		cursor = db_connector.cursor(dictionary = True)
		cursor.execute('''
				select vi.*, cb.icon_url, if(ucp.video_id <=> NULL, 'false', 'true') watched
				from videos vi
				inner join contributors cb
				on  vi.contributor_id = cb.id
				left outer join users_completions ucp
				on vi.id = ucp.video_id and ucp.user_id = {user_id}
				order by serial_no desc
				limit {start}, {count}'''.format(user_id = session['user_id'], start = (page - 1) * perpage, count = perpage))
	else:
		cursor = db_connector.cursor(dictionary = True)
		cursor.execute('''
			select vi.*, cb.icon_url
			from videos vi
			inner join contributors cb
			on  vi.contributor_id = cb.id
			order by serial_no desc
			limit {start}, {count}'''.format(start = (page - 1) * perpage, count = perpage))

	rows = cursor.fetchall()
	cursor.close()

	response = make_response()
	response.data = json.dumps(rows, default=default)
	response.status_code = 200
	return response

@app.route('/videos/count/', methods=['GET'])
def get_videos_count():

	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('select count(id) count from videos')

	cnt_row = cursor.fetchone()
	cursor.close()

	response = make_response()
	response.data = json.dumps(cnt_row, default=default)
	response.status_code = 200
	return response

@app.route('/my/videos/list/', methods=['GET'])
def get_my_videos():
	if 'user_id' not in session:
		response = make_response()
		response.status_code = 401
		return response

	page = get_page_no(request.args.get('page'))
	perpage = get_perpage_no(request.args.get('perpage'))

	# 複数人実況などでvideoが重複して取得される場合があるのでdistinctを付与
	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select distinct vi.*, cb.icon_url, if(ucp.video_id <=> NULL, 'false', 'true') watched
		from videos vi
		inner join videos_contributors vc
		on vi.id = vc.video_id
		inner join users_contributors uc
		on vc.contributor_id = uc.contributor_id
		inner join contributors cb
		on  vi.contributor_id = cb.id
		left outer join users_completions ucp
		on vi.id = ucp.video_id and uc.user_id = ucp.user_id
		where uc.user_id = {user_id}
		order by vi.serial_no desc
		limit {start}, {count}'''.format(user_id = session['user_id'], start = (page - 1) * perpage, count = perpage))

	rows = cursor.fetchall()
	cursor.close()

	response = make_response()
	response.data = json.dumps(rows, default=default)
	response.status_code = 200
	return response

@app.route('/my/videos/count/', methods=['GET'])
def get_my_videos_count():
	if 'user_id' not in session:
		response = make_response()
		response.status_code = 401
		return response

	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select count(vi.id) count
		from videos vi
		inner join videos_contributors vc
		on vi.id = vc.video_id
		inner join users_contributors uc
		on vc.contributor_id = uc.contributor_id
		where uc.user_id = {user_id}'''.format(user_id = session['user_id']))

	cnt_row = cursor.fetchone()
	cursor.close()

	response = make_response()
	response.data = json.dumps(cnt_row, default=default)
	response.status_code = 200
	return response

@app.route('/contributors/<int:contributor_id>/videos/list/', methods=['GET'])
def get_contributor_videos(contributor_id):
	page = get_page_no(request.args.get('page'))
	perpage = get_perpage_no(request.args.get('perpage'))

	if 'user_id' in session:
		cursor = db_connector.cursor(dictionary = True)
		cursor.execute('''
			select vi.*, cb.icon_url, if(ucp.video_id <=> NULL, 'false', 'true') watched
			from videos vi
			inner join videos_contributors vc
			on vi.id = vc.video_id
			inner join users_contributors uc
			on vc.contributor_id = uc.contributor_id
			inner join contributors cb
			on  vi.contributor_id = cb.id
			left outer join users_completions ucp
			on vi.id = ucp.video_id and uc.user_id = ucp.user_id
			where uc.user_id = {user_id} and vc.contributor_id = {contributor_id}
			order by vi.serial_no desc
			limit {start}, {count}'''.format(user_id = session['user_id'], contributor_id = contributor_id, start = (page - 1) * perpage, count = perpage))
	else:
		cursor = db_connector.cursor(dictionary = True)
		cursor.execute('''
			select vi.*, cb.icon_url
			from videos vi
			inner join videos_contributors vc
			on vi.id = vc.video_id
			inner join contributors cb
			on  vi.contributor_id = cb.id
			where vc.contributor_id = {contributor_id}
			order by vi.serial_no desc
			limit {start}, {count}'''.format(contributor_id = contributor_id, start = (page - 1) * perpage, count = perpage))

	rows = cursor.fetchall()
	cursor.close()

	response = make_response()
	response.data = json.dumps(rows, default=default)
	response.status_code = 200
	return response

@app.route('/contributors/<int:contributor_id>/videos/count/', methods=['GET'])
def get_contributor_videos_count(contributor_id):

	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select count(vi.id) count
		from videos vi
		inner join videos_contributors vc
		on vi.id = vc.video_id
		where vc.contributor_id = {contributor_id}'''.format(contributor_id=contributor_id))

	cnt_row = cursor.fetchone()
	cursor.close()

	response = make_response()
	response.data = json.dumps(cnt_row, default=default)
	response.status_code = 200
	return response

@app.route('/my/contributors/', methods=['GET'])
def get_my_contributor():
	if 'user_id' not in session:
		response = make_response()
		response.status_code = 401
		return response

	page = get_page_no(request.args.get('page'))
	perpage = get_perpage_no(request.args.get('perpage'))

	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select cb.*
		from users_contributors uc
		inner join contributors cb
		on uc.contributor_id = cb.id
		where uc.user_id = {user_id}
		order by uc.created_datetime desc
		limit {start}, {count}'''.format(user_id = session['user_id'], start = (page - 1) * perpage, count = perpage))

	rows = cursor.fetchall()
	cursor.close()

	response = make_response()
	response.data = json.dumps(rows, default=default)
	response.status_code = 200
	return response

@app.route('/my/contributors/count/', methods=['GET'])
def get_my_contributor_count():
	if 'user_id' not in session:
		response = make_response()
		response.status_code = 401
		return response

	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select count(uc.contributor_id) count
		from users_contributors uc
		inner join contributors cb
		on uc.contributor_id = cb.id
		where uc.user_id = {user_id}'''.format(user_id = session['user_id']))

	row = cursor.fetchone()
	cursor.close()

	response = make_response()
	response.data = json.dumps(row, default=default)
	response.status_code = 200
	return response

@app.route('/my/contributors/', methods=['POST'])
def post_my_contributor():
	if 'user_id' not in session:
		response = make_response()
		response.status_code = 401
		return response

	post_data = json.loads(request.data.decode(sys.stdin.encoding))
	contributor_id = post_data['id']

	# contributor_idの存在チェック
	if not is_exists_record('contributors', 'id = {0}'.format(contributor_id)):
		res = urllib.request.urlopen('http://api.ce.nicovideo.jp/api/v1/user.info?user_id=' + str(contributor_id))
		body = res.read()
		contributor_xml = xmltodict.parse(body)['nicovideo_user_response']

		if 'vita_option' not in contributor_xml or contributor_xml['vita_option']['user_secret'] == '1':
			response = jsonify(post_data)
			response.status_code = 400
			return response
		else:
			exec_sql('insert into contributors (id, name, icon_url) values ({0}, \'{1}\', \'{2}\')'.format(
				contributor_id, contributor_xml['user']['nickname'], contributor_xml['user']['thumbnail_url']), False)

	# 既に登録されていないかのチェック
	if is_exists_record('users_contributors','user_id = {user_id} and contributor_id = {contributor_id}'.format(
			user_id = session['user_id'], contributor_id = contributor_id)):
		response = jsonify(post_data)
		response.status_code = 400
		return response

	exec_sql('insert into users_contributors (user_id, contributor_id) values ({user_id}, {contributor_id})'.format(
		user_id = session['user_id'], contributor_id = contributor_id), True)

	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select cb.*
		from users_contributors uc
		inner join contributors cb
		on uc.contributor_id = cb.id
		where uc.user_id = {user_id}
		order by uc.created_datetime desc
		limit 0, 20'''.format(user_id = session['user_id']))

	rows = cursor.fetchall()
	cursor.close()

	response = make_response()
	response.data = json.dumps(rows, default=default)
	response.status_code = 201

	return response

@app.route('/my/contributors/', methods=['DELETE'])
def delete_my_contributor():
	if 'user_id' not in session:
		response = make_response()
		response.status_code = 401
		return response

	post_data = json.loads(request.data.decode(sys.stdin.encoding))
	contributor_id = post_data['id']
	perpage = post_data['items_per_page']
	page = post_data['current_page']

	# contributor_idの存在チェック
	if not is_exists_record('contributors', 'id = {0}'.format(contributor_id)):
		response = jsonify(post_data)
		response.status_code = 400
		return response

	# 登録されているかのチェック
	if not is_exists_record('users_contributors', 'user_id = {user_id} and contributor_id = {contributor_id}'.format(
			user_id = session['user_id'], contributor_id = contributor_id)):
		response = jsonify(post_data)
		response.status_code = 400
		return response

	exec_sql('delete from users_contributors where user_id = {user_id} and contributor_id = {contributor_id}'.format(
		user_id = session['user_id'], contributor_id = contributor_id), True)

	cursor = db_connector.cursor(dictionary = True)
	cursor.execute('''
		select cb.*
		from users_contributors uc
		inner join contributors cb
		on uc.contributor_id = cb.id
		where uc.user_id = {user_id}
		order by uc.created_datetime desc
		limit {start}, {count}'''.format(user_id = session['user_id'], start = (page - 1) * perpage, count = perpage))

	rows = cursor.fetchall()
	cursor.close()

	response = make_response()
	response.data = json.dumps(rows, default=default)
	response.status_code = 201

	return response

@app.route('/videos/<int:video_id>/completion/', methods=['POST'])
def post_completion(video_id):
	if 'user_id' not in session:
		response = make_response()
		response.status_code = 401
		return response

	# videoの存在チェック
	if not is_exists_record('videos', 'id = {0}'.format(video_id)):
		response = make_response()
		response.status_code = 400
		return response

	# completionの存在チェック
	if is_exists_record('completions', 'video_id = {0}'.format(video_id)):
		# 既に視聴済みの場合は、レコードを削除し未視聴とする
		if is_exists_record('users_completions', 'user_id = {0} and video_id = {1}'.format(1, video_id)):
			exec_sql('delete from users_completions where user_id = {user_id} and video_id = {video_id}'.format(
				user_id = session['user_id'], video_id = video_id), True)
			response = jsonify({'isWatched': 'false'})
			response.status_code = 201
			return response
	else:
		exec_sql('insert into completions (video_id) values ({0})'.format(video_id), False)

	exec_sql('insert into users_completions (user_id, video_id) values ({user_id}, {video_id})'.format(user_id = session['user_id'], video_id = video_id), True)

	response = jsonify({'isWatched': 'true'})
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
リクエストパラメータからページあたりの数を取得する

@type arg_perpage: str
@param arg_perpage: リクエストパラメータで指定されたperpage
@return リクエストパラメータのperpageに有効な値が設定されている場合は、
        リクエストパラメータのperpageを数値に変換し返却。
        有効でない値の場合は、20を返却。
"""
def get_perpage_no(param_perpage):
	perpage = 20
	if param_perpage is not None and param_perpage.isdigit() and int(param_perpage) > 0:
		perpage = int(param_perpage)

	return perpage

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
