import json
import numpy as np
import re
import boto
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

s3 = boto.client('s3')
bucket = 'moodsongrecommend'
TOKENIZER = pickle.load(s3.get_object(Bucket=bucket, key='tokenizer.pkl'))
MODEL = load_model(s3.get_object(Bucket=bucket, key='Glove_embedding_CNN_LSTM_model.h5'))
MAX_LEN = 41
MAX_FEATURES = 5000
print('Model Loaded')


def lambda_handler(event, context):
    data = event['thought']
    data = prepare_input(data)
    return {
        'statusCode': 200,
        'body': np.argmax(MODEL.predict(data), axis=-1)[0]
    }


# FUNCTION TO PREPARE DATA FOR MODEL INPUT
def prepare_input(inp):
    inp = inp.lower()
    inp = _remove_username(inp)
    inp = _remove_punctuation(inp)
    inp = _remove_emojis(inp)
    inp = _remove_misc(inp)
    padded = _get_sequences_and_pad(inp)
    return padded


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
    padded = pad_sequences(sequences=sequences, maxlen=MAX_LEN, padding='post')
    return padded
