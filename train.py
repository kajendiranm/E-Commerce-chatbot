import json 
import numpy as np 
import tensorflow
from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense, Embedding, LSTM
from keras import layers
# from keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.text import Tokenizer
from keras.utils import pad_sequences
from sklearn.preprocessing import LabelEncoder
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re
from sklearn.model_selection import train_test_split
from kerastuner.tuners import RandomSearch
from kerastuner.engine.hyperparameters import HyperParameters
import pickle

# Download required NLTK resources
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Load stop words
stop_words = set(stopwords.words('english'))

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

with open('dataset.json') as file:
    data = json.load(file)

training_sentences = []
training_labels = []
labels = []
responses = []

# Preprocess the text
def preprocess_text(text):
    # Remove special characters and numbers
    text = re.sub('[^a-zA-Z]', ' ', text)
    
    # Tokenize the text
    words = nltk.word_tokenize(text)
    
    # Lemmatize and remove stop words
    words = [lemmatizer.lemmatize(word.lower()) for word in words if word.lower() not in stop_words]
    
    return ' '.join(words)

for intent in data['questions']:
    if len(intent['tags']) > 0:
        training_sentences.append(preprocess_text(intent['question']))
        training_labels.append(intent['tags'][0])
        responses.append(intent['answer'])
        
        if intent['tags'][0] not in labels:
            labels.append(intent['tags'][0])
        
num_classes = len(labels)
lbl_encoder = LabelEncoder()
lbl_encoder.fit(training_labels)
training_labels = lbl_encoder.transform(training_labels)
vocab_size = 2000
embedding_dim = 16
max_len = 200
oov_token = "<OOV>"

tokenizer = Tokenizer(num_words=vocab_size, oov_token=oov_token) # adding out of vocabulary token
tokenizer.fit_on_texts(training_sentences)
word_index = tokenizer.word_index
sequences = tokenizer.texts_to_sequences(training_sentences)
padded_sequences = pad_sequences(sequences, truncating='post', maxlen=max_len)

# Define the model builder function for Keras Tuner
def build_model(hp):
    model = Sequential()
    model.add(Embedding(vocab_size, embedding_dim, input_length=max_len))
    model.add(LSTM(units=hp.Int('units', min_value=50, max_value=150, step=10), return_sequences=True))
    model.add(LSTM(units=hp.Int('units', min_value=50, max_value=150, step=10)))

    for i in range(hp.Int('num_layers', 1, 20)):
        model.add(layers.Dense(units=hp.Int('units_' + str(i), min_value=16, max_value=256, step=16), activation='relu'))

    model.add(Dense(num_classes, activation='softmax'))

    model.compile(optimizer=keras.optimizers.Adam(hp.Choice('learning_rate', [1e-2, 1e-3, 1e-4])), loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    return model


model = Sequential()
model.add(Embedding(vocab_size, embedding_dim))
model.add(LSTM(110, return_sequences=True, input_shape=(max_len, embedding_dim)))
model.add(LSTM(110))
model.add(Dense(208, activation='relu'))
model.add(Dense(num_classes, activation='softmax'))
model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.01), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.summary()


epochs = 200
print(len(padded_sequences))
print(len(training_labels))



# Train the model on the training set
history = model.fit(padded_sequences, np.array(training_labels), epochs=epochs)



# saving model
model.save("chat_model.h5")

# saving tokenizer
with open('tokenizer.pickle', 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
# saving label encoder
with open('label_encoder.pickle', 'wb') as ecn_file:
    pickle.dump(lbl_encoder, ecn_file, protocol=pickle.HIGHEST_PROTOCOL)