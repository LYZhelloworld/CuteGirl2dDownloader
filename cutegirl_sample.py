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
timestamp_start = datetime.datetime(
    2018, 3, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp()
timestamp_end = datetime.datetime(
    2018, 4, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp()
# TODO: Change the variables above

target = 'CuteGirl_2D'  # Twitter screen name
buffer_size = 8192  # Buffer size when downloading
result_dict = {}


def get_images(result_dict, timestamp_start, timestamp_end):
    'Get tweets from timeline.'
    api = twitter.Api(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token_key=access_token_key,
        access_token_secret=access_token_secret)
    result = api.GetUserTimeline(
        screen_name=target, trim_user=True, exclude_replies=True)
    next_max_id = process_result(
        result_dict, result, timestamp_start, timestamp_end)
    while next_max_id:
        result = api.GetUserTimeline(
            screen_name=target,
            trim_user=True,
            exclude_replies=True,
            max_id=next_max_id)
        next_max_id = process_result(
            result_dict, result, timestamp_start, timestamp_end)


def process_result(result_dict, result, timestamp_start, timestamp_end):
    'Process each tweet and save it to the dictionary.'
    for r in result:
        if r.id in result_dict:
            continue
        if datetime.datetime.utcfromtimestamp(
                r.created_at_in_seconds) > datetime.datetime.utcfromtimestamp(timestamp_end):
            continue  # Skip
        if datetime.datetime.utcfromtimestamp(
                r.created_at_in_seconds) < datetime.datetime.utcfromtimestamp(timestamp_start):
            return None  # Return None to stop loop
        # Format: Illustrator / xxxxx
        illustrator_match = re.search(r'(?<=^Illustrator / )(.*)', r.text)
        if illustrator_match:
            illustrator = illustrator_match.group(0)
        else:
            illustrator = None
        if r.media:
            # Since the account sometimes posts multiple images in one tweet,
            # we need to use list here.
            if r.id not in result_dict:
                result_dict[r.id] = []
            for m in r.media:
                media_url = process_media(m)
                if media_url:
                    result_dict[r.id].append(
                        (media_url, illustrator, m.id, process_datetime(r.created_at_in_seconds)))
    return result[-1].id  # Last id


def process_media(media):
    'Get URL of the media. Non-image resources will be ignored.'
    if not media:
        return None
    if media.type != 'photo':
        return None
    return media.media_url_https


def process_datetime(timestamp):
    'Convert timestamp into YYMMDDhhmmss.'
    return datetime.datetime.utcfromtimestamp(
        timestamp).strftime('%Y%m%d%H%M%S')


def gen_filename(root, illustrator, date, media_id):
    'Generate filename: [Date][Illustrator]ID.jpg. Illustrator will be "Unknown Illustrator" if N/A.'
    illustrator_path = illustrator
    if illustrator is None:
        illustrator = 'Unknown Illustrator'
        illustrator_path = ''
    return os.path.join(
        root,
        illustrator_path,
        '[{date}][{illustrator}]{media_id}.jpg'.format(
            illustrator=illustrator,
            date=date,
            media_id=media_id))


def save_images(result_dict, saving_path):
    'Download images from the links.'
    if not os.path.exists(saving_path):
        os.makedirs(saving_path)
    for key in result_dict:
        for item in result_dict[key]:
            filename = gen_filename(
                root=saving_path,
                illustrator=item[1],
                date=item[3],
                media_id=item[2])
            url = item[0]
            req = urllib.request.urlopen(url)
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            with open(filename, 'wb') as fp:
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
