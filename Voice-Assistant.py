# -*- coding: utf-8 -*-
"""Project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZCQtFs5C2SfHm1OgzuUvQc9hWIibKvRw
"""

import numpy as np
from scipy.io import wavfile
import librosa
from sklearn.preprocessing import LabelEncoder
from keras.utils import np_utils
import warnings
import os
import IPython.display as ipd
from sklearn.model_selection import train_test_split
from keras.layers import Dense, Dropout, Flatten, Conv1D, Input, MaxPooling1D
from keras.models import Model, load_model
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras import backend as K
from matplotlib import pyplot as plt
import random

#acsessing to the full numpy array
np.set_printoptions(threshold=np.inf)

#ignore the warnings
warnings.filterwarnings('ignore')
#prevent tensorflow from printing an error about memory and gpu resources allocation
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

#obtaining the dataset
path = 'Data/'
labels = os.listdir(path)
print(labels)

#printing numbers of recordings
number_of_recordings = []
for label in labels:
    waves = [f for f in os.listdir(path + '/' + label) if f.endswith('.wav')]
    number_of_recordings.append(len(waves))
print(number_of_recordings)


voice_waves = []
voice_labels = []
for label in labels:
    print(label)
    waves = [f for f in os.listdir(path + '/' + label) if f.endswith('.wav')]
    for wave in waves:
        #Load an audio file as a floating point time series
        samples, sampling_rate = librosa.load(path + '/' + label + '/' + wave, sr=16000)
        #defining a new sampling rate
        samples = librosa.resample(samples, sampling_rate, 8000)
        samples = librosa.util.fix_length(samples, 8000, axis=-1)

        if len(samples) == 8000:
            voice_waves.append(samples)
            voice_labels.append(label)

#Encode target labels with value between 0 and classes
encoder = LabelEncoder()
y = encoder.fit_transform(voice_labels)
classes = list(encoder.classes_)
#convert array of labeled data(from 0 to nb_classes - 1) to one-hot vector
y = np_utils.to_categorical(y, num_classes=len(labels))
voice_waves = np.array(voice_waves).reshape(-1, 8000, 1)
#defining test and train data
x_tr, x_val, y_tr, y_val = train_test_split(np.array(voice_waves), np.array(y), stratify=y, test_size=0.2,random_state=843, shuffle=True)
                                        
K.clear_session()
inputs = Input(shape=(8000, 1))

#CNN
conv = Conv1D(8, 13, padding='valid', activation='relu', strides=1)(inputs)
conv = MaxPooling1D(3)(conv)
#preventing overfit
conv = Dropout(0.2)(conv)
conv = Conv1D(16, 11, padding='valid', activation='relu', strides=1)(conv)
conv = MaxPooling1D(3)(conv)
conv = Dropout(0.2)(conv)
conv = Conv1D(32, 9, padding='valid', activation='relu', strides=1)(conv)
conv = MaxPooling1D(3)(conv)
conv = Dropout(0.2)(conv)
conv = Conv1D(64, 7, padding='valid', activation='relu', strides=1)(conv)
conv = MaxPooling1D(3)(conv)
conv = Dropout(0.2)(conv)
# Flatten layer
conv = Flatten()(conv)
# Dense Layer
conv = Dense(256, activation='relu')(conv)
conv = Dropout(0.2)(conv)
conv = Dense(128, activation='relu')(conv)
conv = Dropout(0.2)(conv)

outputs = Dense(len(labels), activation='softmax')(conv)
model = Model(inputs, outputs)
model.compile(loss='kullback_leibler_divergence', optimizer='adam', metrics=['accuracy'])

if os.path.exists('classification_model2.h5'):
    model = load_model('classification_model2.h5')
#optimization
else:
    Stop = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=10, min_delta=0.00001)
    Checkpoint = ModelCheckpoint('best_model.hdf5', monitor='val_acc', verbose=1, save_best_only=True, mode='max')
    history = model.fit(x_tr, y_tr, epochs=30, callbacks=[Stop, Checkpoint], batch_size=25, validation_data=(x_val, y_val))
    model.save('classification_model2.h5')
    plt.plot(history.history['loss'], label='train')
    plt.plot(history.history['val_loss'], label='test')
    plt.legend()
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.show()

def predict(audio):
    prob = model.predict(audio.reshape(1, 8000, 1))
    ind = np.argmax(prob[0])
    return classes[ind]
#printing 5 random voices prediction results
for i in range(5):
    index = random.randint(0, len(x_val) - 1)
    samples = x_val[index].ravel()
    ipd.Audio(samples, rate=8000)
    print("Audio is :", classes[np.argmax(y_val[index])], "and the prediction will be : ", predict(samples))