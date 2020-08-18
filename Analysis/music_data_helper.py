'''
This script helps in reading data from two different databases, transforms the data and stores into a single database
'''

import sqlite3
import tqdm
import json
import pandas as pd

#CREATE CONNECTION TO DB
conn = sqlite3.connect('lastfm_tags.db')

# GET ALL THE TRACK IDS
all_tid = conn.execute('SELECT DISTINCT * FROM tids')
all_tid = all_tid.fetchall()
all_tid = [row[0] for row in all_tid]

# EMPTY DICT TO STORE TRACKID WITH ITS TAGS AS KEY VALUE PAIR
track_tag_dict = dict()

for tid in tqdm.tqdm(all_tid):
    sql = "SELECT tags.tag, tid_tag.val FROM tid_tag, tids, tags WHERE tags.ROWID=tid_tag.tag AND tid_tag.tid=tids.ROWID and tids.tid = '{}'".format(tid)
    res = conn.execute(sql)
    data = res.fetchall()
    tags = [row[0] for row in data]
    track_tag_dict[tid] = tags

# STORE THE DICT OBJECT AS JSON
with open('trackid-tags.json', 'w') as f:
    json.dump(track_tag_dict, f)

# CREATE A NEW DATABASE WHICH CONTAINS SONG WITH TAGS - RELIGIOUS, RELIGION, CHEER, CHEERFUL, CALM, DANCE, HAPPY, JOY, JOYFULL
meta_db = 'meta.db'

# QUERY TO GET ID OF THE MENTIONED TAGS
tags = ('religious', 'religion', 'cheer', 'cheerful', 'calm', 'dance', 'happy', 'joy', 'joyful', 'joyfull')
tag_idx_dict = dict()
tag_trackid_dict = dict()
tag_rid_dict = dict()

for tag in tqdm.tqdm(tags):
    sql = "SELECT _rowid_ from tags WHERE lower(tag) = '{}'".format(tag)
    idx = conn.execute(sql)
    idx = idx.fetchall()
    tag_idx_dict[tag] = idx[0][0]

# STORE THE DICT OBJECT AS JSON
with open('tags-idx.json', 'w') as f:
    json.dump(tag_idx_dict, f)

# GET ROWID BASED ON TAG IDX 
for k,v in tqdm.tqdm(tag_idx_dict.items()):
    sql = "SELECT _rowid_ FROM tid_tag WHERE lower(tag) = '{}'".format(v)
    r_id = conn.execute(sql)
    r_id = r_id.fetchall()
    tag_rid_dict[k] = [elem[0] for elem in r_id]

# GET TRACK IDS
for k,v in tqdm.tqdm(tag_rid_dict.items()):
    sql = "SELECT tid FROM tids WHERE _rowid_ IN {0}".format(tuple(v))
    track_id = conn.execute(sql)
    track_id = track_id.fetchall()
    tag_trackid_dict[k] = [elem[0] for elem in track_id]
    

# STORE THE DICT OBJECT AS JSON
with open('tags-trackid.json', 'w') as f:
    json.dump(tag_trackid_dict, f)

conn.close()

# CREATE CONNECTION TO SECON DATABASE CONTANING SONG METADATA
conn = sqlite3.connect('track_metadata.db')

# TARCK POOL
track_id_pool = [v for v in tag_trackid_dict.values()]
track_id_pool = tuple([item for sublist in track_id_pool for item in sublist])

# GET INFO - title, artist, list
sql = 'SELECT track_id, title, artist_name, year FROM songs WHERE track_id IN {0}'.format(track_id_pool)
data = conn.execute(sql)
data = data.fetchall()
conn.close()

conn = sqlite3.connect(meta_db)
pd.DataFrame(data, columns=['track_id', 'title', 'artist', 'year']).to_sql('songs_mini', con=conn)
conn.close()