from flask import Flask, render_template, url_for, redirect, request
import re
import json
import requests
import random
import os
import sqlite3

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
API_URL = 'https://csxvmmfmg9.execute-api.us-east-1.amazonaws.com/model1/recommend-mood'
app = Flask(__name__, root_path=DIR_PATH)
NUM_OF_TRACKS = 5
DB = sqlite3.connect(DIR_PATH + r'/data/meta.db', check_same_thread=False)
with open(DIR_PATH + r'/data/tags-trackid.json', 'r') as f:
    DATA = json.load(f)


@app.route("/", methods=['GET'])
def home():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    error = None
    if request.method == 'POST':
        data = request.form['thought']

        # FROM VALIDATIONS
        if data.strip() == '':
            error = 'Textbox is empty!'
        elif len(re.split(',| ', data)) < 3:
            error = 'Please enter atleast 3 words!'
        elif min(set([len(word) for word in re.split(',| ', data)])) == 1:
            error = "Please don't enter single characters"
        else:
            pass

        if error is not None:
            redirect('/', code=302)
            return render_template('index.html', error=error)
        else:
            mood = requests.post(API_URL, data={'thought': data}).json()['body']
            display_msg = beautify_output_msg(mood)
            songs = recommend_song(mood)
            return render_template('predict.html', value=display_msg, songs=songs)
    else:
        return redirect('/', code=302)


# CUSTOM MESSAGES FOR USER
def beautify_output_msg(mood):
    if mood == 0:
        msg = "You seem pissed. Here are some songs to help you calm down"
    elif mood == 1:
        msg = "Don't be afraid. Here are some religious tunes for you"
    elif mood == 2:
        msg = "Wow, you sound joyful. Enjoy these beats"
    else:
        msg = "Aww don't be sad. These will surely cheer you up!"
    return msg


'''
Currently it is rule based. In future similar tracks will be displayed to the 
user when the user likes a particular recommendation
'''


# SONG FOR USERS
def recommend_song(mood):
    if mood == 0:
        return _get_calm_songs()
    elif mood == 1:
        return _get_religious_songs()
    elif mood == 2:
        return _get_joyful_songs()
    else:
        return _get_cheerfull_songs()


def _get_calm_songs():
    song_pool = DATA["calm"]
    query = 'SELECT * FROM songs_mini WHERE track_id IN {0}'.format(
        tuple(random.choices(song_pool, k=NUM_OF_TRACKS)))
    return DB.execute(query).fetchall()


def _get_religious_songs():
    song_pool = DATA["religious"] + DATA['religion']
    query = 'SELECT * FROM songs_mini WHERE track_id IN {0}'.format(
        tuple(random.choices(song_pool, k=NUM_OF_TRACKS)))
    return DB.execute(query).fetchall()


def _get_joyful_songs():
    song_pool = DATA["dance"] + DATA['happy'] + DATA['joy'] + DATA['joyful'] + DATA['joyfull']
    query = 'SELECT * FROM songs_mini WHERE track_id IN {0}'.format(
        tuple(random.choices(song_pool, k=NUM_OF_TRACKS)))
    return DB.execute(query).fetchall()


def _get_cheerfull_songs():
    song_pool = DATA["cheer"] + DATA['cheerful'] + DATA['happy']
    query = 'SELECT * FROM songs_mini WHERE track_id IN {0}'.format(
        tuple(random.choices(song_pool, k=NUM_OF_TRACKS)))
    return DB.execute(query).fetchall()
