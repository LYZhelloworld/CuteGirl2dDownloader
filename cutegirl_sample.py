#!/usr/bin/python3
# -*- coding: utf-8 -*-

import twitter
import datetime
import re
import urllib.request
import os.path

# TODO: Change the variables below
consumer_key = 'sample_key'
consumer_secret = 'sample_secret'
access_token_key = 'sample_token_key'
access_token_secret = 'sample_token_secret'
saving_path = '.\\result'
# UTC time only
timestamp_start = datetime.datetime(2018,3,1,0,0,0,0, tzinfo=datetime.timezone.utc).timestamp()
timestamp_end = datetime.datetime(2018,4,1,0,0,0,0, tzinfo=datetime.timezone.utc).timestamp()
# TODO: Change the variables above

target = 'CuteGirl_2D' # Twitter screen name
buffer_size = 8192 # Buffer size when downloading
result_dict = {}

def get_images(result_dict, timestamp_start, timestamp_end):
	'Get tweets from timeline.'
	api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token_key=access_token_key, access_token_secret=access_token_secret)
	result = api.GetUserTimeline(screen_name=target, trim_user=True, exclude_replies=True)
	next_max_id = process_result(result_dict, result, timestamp_start, timestamp_end)
	while next_max_id:
		result = api.GetUserTimeline(screen_name=target, trim_user=True, exclude_replies=True, max_id=next_max_id)
		next_max_id = process_result(result_dict, result, timestamp_start, timestamp_end)

def process_result(result_dict, result, timestamp_start, timestamp_end):
	'Process each tweet and save it to the dictionary.'
	for r in result:
		if r.id in result_dict:
			continue
		if datetime.datetime.utcfromtimestamp(r.created_at_in_seconds) > datetime.datetime.utcfromtimestamp(timestamp_end):
			continue # Skip
		if datetime.datetime.utcfromtimestamp(r.created_at_in_seconds) < datetime.datetime.utcfromtimestamp(timestamp_start):
			return None # Return None to stop loop
		illustrator_match = re.search(r'(?<=^Illustrator / )(.*)', r.text) # Format: Illustrator / xxxxx
		if illustrator_match:
			illustrator = illustrator_match.group(0)
		else:
			illustrator = None
		if r.media:
			# Only process first media (since this account posts one image per tweet only)
			m = r.media[0]
			media_url = process_media(m, illustrator)
			if media_url:
				result_dict[r.id] = (media_url, illustrator, m.id, process_datetime(r.created_at_in_seconds))
	return result[-1].id # Last id

def process_media(media, illustrator):
	'Get URL of the media. Non-image resources will be ignored.'
	if not media:
		return None
	if media.type != 'photo':
		return None
	return media.media_url_https

def process_datetime(timestamp):
	'Convert timestamp into YYMMDDhhmmss.'
	return datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y%m%d%H%M%S')

def gen_filename(illustrator, date, media_id):
	'Generate filename: [Date][Illustrator]ID.jpg. Illustrator will be "Unknown Illustrator" if N/A.'
	if illustrator is None:
		illustrator = 'Unknown Illustrator'
	return '[{date}][{illustrator}]{media_id}.jpg'.format(illustrator=illustrator, date=date, media_id=media_id)

def save_images(result_dict, saving_path):
	'Download images from the links.'
	if not os.path.exists(saving_path):
		os.makedirs(saving_path)
	for key in result_dict:
		filename = gen_filename(illustrator=result_dict[key][1], date=result_dict[key][3], media_id=result_dict[key][2])
		url = result_dict[key][0]
		req = urllib.request.urlopen(url)
		with open(saving_path + '\\' + filename, 'wb') as fp:
			while True:
				buf = req.read(buffer_size)
				if not buf:
					break
				fp.write(buf)
		print('Download complete: ' + filename)

if __name__ == '__main__':
	get_images(result_dict, timestamp_start, timestamp_end)
	print('Retrieved {0} result(s).'.format(len(result_dict)))
	save_images(result_dict, saving_path)