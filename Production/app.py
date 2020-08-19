import re
import numpy as np
from flask import Flask, request, jsonify, render_template, url_for, redirect
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import json
import random
import sqlite3
import pickle
import os

DIRNAME = os.path.dirname(os.path.realpath(__file__))
MAXLEN = 41
MAX_FEATURES = 5000
#{0: 'anger', 1: 'fear', 2: 'joy', 3: 'sadness'}

with open(DIRNAME + r'/data/tokenizer.pkl', 'rb') as p:
    TOKENIZER = pickle.load(p)
with open(DIRNAME + r'/data/tags-trackid.json', 'r') as f:
    DATA = json.load(f)
with open(DIRNAME + r'/data/tags-trackid.json', 'r') as f:
    LABELS = json.load(f)

NUM_OF_TRACKS = 5
DB = sqlite3.connect(DIRNAME + r'/data/meta.db', check_same_thread=False)
MODEL = load_model(DIRNAME + r'/data/Glove_embedding_CNN_LSTM_model.h5')

app = Flask(__name__, root_path=DIRNAME)
global display_msg, songs

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        data = request.form['thought']
        data = prepare_input(data)
        pred = np.argmax(MODEL.predict(data), axis=-1)[0]
        display_msg = beautify_output_msg(pred)
        songs = recommed_song(pred)
        return render_template('predict.html', value=display_msg, songs=songs)
    else:
        return redirect('/', code=302)

@app.route('/similar', methods=['GET'])
def get_recommendation():
    return render_template('similar.html')


# FUNCTION TO PREPARE DATA FOR MODEL INPUT
def prepare_input(inp):
    inp = inp.lower()
    inp = _remove_username(inp)
    inp = _remove_punctuation(inp)
    inp = _remove_emojis(inp)
    inp = _remove_misc(inp)
    padded = _get_sequences_and_pad(inp)
    return padded

# CUSTOM MESSAGES FOR USER
def beautify_output_msg(mood):
    msg = ''
    if mood == 0:
        msg = "You seem pissed. Here are some songs to help you calm down"
    elif mood == 1:
        msg = "Don't be afraid. Here are some religious tunes for you"
    elif mood == 2:
        msg = "Wow, you sound joyful. Enjoy these beats"
    else:
        msg = "Aww don't be sad. These will surely cheer you up!"
    return msg 

# SONG FOR USERS
# Currently it is rule based. In future similar tracks will be displayed to the user when the user likes a particular recommendation
def recommed_song(mood):
    if mood == 0:
        return _get_calm_songs()
    elif mood == 1:
        return _get_religious_songs()
    elif mood == 2:
        return _get_joyful_songs()
    else:
        return _get_cheerfull_songs()

# HELPER FUNCTIONS 
def _remove_username(inp):
    pat = '@[^\s]+'
    return re.sub(pat, '', inp)

def _remove_punctuation(inp):
    pat = '[!#?,.:";]'
    return re.sub(pat, '', inp)

def _remove_emojis(inp):
    pat = re.compile(pattern = "["
      u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags = re.UNICODE)
    return pat.sub(r'', inp)

def _remove_misc(inp):
    inp = inp.replace("\\", "")
    inp = inp.replace("&amp", "")
    return inp

def _get_sequences_and_pad(inp):
    sequences = TOKENIZER.texts_to_sequences([inp])
    padded = pad_sequences(sequences=sequences, maxlen=MAXLEN, padding='post')
    return padded

def _get_calm_songs():
    song_pool = DATA["calm"]
    query = 'SELECT * FROM songs_mini WHERE track_id IN {0}'.format(tuple(random.choices(song_pool, k=NUM_OF_TRACKS)))
    return DB.execute(query).fetchall()


def _get_religious_songs():
    song_pool = DATA["religious"] + DATA['religion']
    query = 'SELECT * FROM songs_mini WHERE track_id IN {0}'.format(tuple(random.choices(song_pool, k=NUM_OF_TRACKS)))
    return DB.execute(query).fetchall()


def _get_joyful_songs():
    song_pool = DATA["dance"] + DATA['happy'] + DATA['joy'] + DATA['joyful'] + DATA['joyfull']
    query = 'SELECT * FROM songs_mini WHERE track_id IN {0}'.format(tuple(random.choices(song_pool, k=NUM_OF_TRACKS)))
    return DB.execute(query).fetchall()


def _get_cheerfull_songs():
    song_pool = DATA["cheer"] + DATA['cheerful'] + DATA['happy']
    query = 'SELECT * FROM songs_mini WHERE track_id IN {0}'.format(tuple(random.choices(song_pool, k=NUM_OF_TRACKS)))
    return DB.execute(query).fetchall()

# RUN SERVER
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
