#Importing Libraries
import numpy as np
import cv2
import time
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf

from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import GlobalAveragePooling2D,Dense,Input,Conv2D, Dropout

from tensorflow.keras.preprocessing.image import ImageDataGenerator

#Define network
IMG_SIZE = 224                      # VGG19
IMG_SHAPE = (IMG_SIZE, IMG_SIZE, 3)

def net():
    base_model = tf.keras.applications.VGG19(input_shape=IMG_SHAPE,
                                                   include_top=True,
                                                   weights='imagenet')

    # define new empty model
    model = Sequential()

    # add all layers except output from VGG19 to new model
    for layer in base_model.layers[:-3]:
        model.add(layer)

    base_model.trainable = False

    # freeze all weights
    # for layer in model.layers:
    #     layer.trainable = False

    # add dropout layer and new output layer
    model.add(Dropout(0.3))
    model.add(Dense(units=2048, activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(units=1024, activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(100, activation='softmax'))

    model.summary()    
    return model

model = net()
model.compile(loss = 'categorical_crossentropy',optimizer ='adam', metrics=['accuracy'])
model_name = 'cifar100_VGG19'

# Load the CIFAR-100 dataset
cifar100 = tf.keras.datasets.cifar100

# load dataset
(X_train, Y_train) , (X_test, Y_test) = cifar100.load_data()

# Shuffle only the training data along axis 0 
def shuffle_train_data(X_train, Y_train): 
    """called after each epoch""" 
    perm = np.random.permutation(len(Y_train)) 
    Xtr_shuf = X_train[perm] 
    Ytr_shuf = Y_train[perm] 
    
    return Xtr_shuf, Ytr_shuf 

train_size = 800
test_size = 800
training_epoch = 1

time0 = time.time()

import os.path
if os.path.isfile(model_name+'.h5'):
    model.load_weights(model_name+'.h5')

for idx in range(training_epoch*25):

    X_shuffled, Y_shuffled = shuffle_train_data(X_train, Y_train)
    (X_train_new, Y_train_new) = X_shuffled[:train_size, ...], Y_shuffled[:train_size, ...] 

    datagen = ImageDataGenerator(
        featurewise_center=True,
        featurewise_std_normalization=True,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True)
    # compute quantities required for featurewise normalization
    # (std, mean, and principal components if ZCA whitening is applied)
    datagen.fit(X_train_new)

    x_batch = []
    y_batch = []

    for i in range(train_size):
        img = cv2.resize(X_train_new[i], (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_CUBIC)
        x_batch.append(img)
        y_batch.append(Y_train_new[i])

    x_batch = np.array(x_batch)
    y_batch = np.array(y_batch)
    y_batch = tf.keras.utils.to_categorical(y_batch, 100)

    x_batch = x_batch/255.
    model.fit(x_batch, y_batch, batch_size = 100, epochs=5, verbose=1)

    if (idx+1)%25 == 0:
        x_batch_val = []
        y_batch_val = []
        for i in range(test_size):
            img = cv2.resize(X_test[i], (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_CUBIC)
            x_batch_val.append(img)
            y_batch_val.append(Y_test[i])

        x_batch_val = np.array(x_batch_val)
        y_batch_val = np.array(y_batch_val)
        y_batch_val = tf.keras.utils.to_categorical(y_batch_val, 100)

        x_batch_val = x_batch_val/255.
        # eval = model.evaluate(x_batch_val, y_batch_val, batch_size = 256)
        model.evaluate(x_batch_val, y_batch_val, batch_size = 100 )
        # print(f"Validation loss: {eval[0]}\tValidation Acc: {eval[1]}\n")
        # print(eval,"\n")
        model.save_weights(model_name+'.h5', overwrite=True)
        print("Trained epoch :",(idx+1)*5," Model saved!!!\n")

time3 = time.time()
print(training_epoch*5," epochs time :",time3-time0)

