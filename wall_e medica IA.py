# -*- coding: utf-8 -*-
"""Wall-e_V3

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1aY_ifBn8fVp-q5lrti8Cvo07ddNu-Dso

###Descargas
"""

!pip install wfdb

"""#Principal

Este conjunto de datos se compone de dos colecciones de señales de latidos cardíacos derivadas de dos conjuntos de datos famosos en la clasificación de latidos cardíacos, el conjunto de datos de arritmia MIT-BIH y la base de datos de diagnóstico de ECG de PTB. La cantidad de muestras en ambas colecciones es lo suficientemente grande como para entrenar una red neuronal profunda.

##Importamos librerias y descargamos el dataset
"""

from google.colab import drive
drive.mount('/content/drive')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import collections
import tensorflow as tf

from keras import optimizers, losses, activations, models
from keras.callbacks import ModelCheckpoint, EarlyStopping, LearningRateScheduler, ReduceLROnPlateau
from keras.layers import Dense, Input, Dropout, Convolution1D, MaxPool1D, GlobalMaxPool1D, GlobalAveragePooling1D, \
    concatenate, Masking, SimpleRNN, GRU, LSTM, Bidirectional, Add
from keras.utils import plot_model
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, auc, precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_curve, roc_curve

"""###Datasets"""

df_1 = pd.read_csv("/content/drive/MyDrive/dataset/ptbdb_normal.csv", header=None)
df_2 = pd.read_csv("/content/drive/MyDrive/dataset/ptbdb_abnormal.csv", header=None)
df = pd.concat([df_1, df_2])

print(df_1.shape)
print(df_2.shape)

df.head(5)

"""##desarrollo

"""

print("Tenemos un total de {} muestras de datos, correspondientes a {} puntos en el tiempo.".format(df.shape[0], df.shape[1]-1))
freq_normal = (df_1.shape[0]/df.shape[0])*100
print("tenemos {} NORMAL data points, Por lo tanto {:.2f}% de la data.".format(df_1.shape[0], freq_normal))
freq_abnormal = (df_2.shape[0]/df.shape[0])*100
print("tenemos {} ABNORMAL data points, por lo tamto {:.2f}% de la data.\n".format(df_2.shape[0], freq_abnormal))
frequencies = [freq_abnormal, freq_normal]

fig, ax = plt.subplots(figsize=(12,5))
df.iloc[:,187].value_counts().plot(ax=ax, kind='bar')
ax.set_xticklabels(['Abnormal', 'Normal'])
for line in range(2):
     ax.text(line-0.05, frequencies[line]+700,s=str(round(frequencies[line],2))+"%", horizontalalignment='left', size='medium', color='black', weight='semibold')
ax.set_title("Frequency of PTB")

print("Visual plot of how normal heartbeat looks like and how an irregular heartbeat looks like.")
print(df_1.shape)
df_1.iloc[0,:80]
x_length = 135
x=np.arange(187)/1000
plt.figure(figsize=(15,5))
plt.plot(x[:x_length],df_1.iloc[1,:x_length].ravel(),label='Normal')
plt.plot(x[:x_length],df_2.iloc[6,:x_length].ravel(),label='Abnormal')
plt.legend()
plt.xlabel('Time(sec)')
plt.ylabel("Amplitude")
plt.title("ECG Signal")
plt.tight_layout()
plt.show()

"""### Separamos el conjunto de datos"""

df_train, df_test = train_test_split(df, test_size=0.2, random_state=1337, stratify=df[187])


Y = np.array(df_train[187].values).astype(np.int8) #Esta línea de código crea un array NumPy Y que contiene la variable de salida o etiquetas para cada registro en el conjunto de datos de entrenamiento 
X = np.array(df_train[list(range(187))].values)[..., np.newaxis] #Esta línea de código crea un array NumPy X que contiene las señales de EEG (los datos de entrada) para cada registro en el conjunto de datos de entrenamiento. 

Y_test = np.array(df_test[187].values).astype(np.int8)
X_test = np.array(df_test[list(range(187))].values)[..., np.newaxis]

print(Y.shape)
print(X.shape)
print(Y_test.shape)
print(X_test.shape)

plt.hist(df_train[187])
plt.title('Histogram of PTB classes')
plt.xlabel('Class')
plt.ylabel('Frequency')
plt.show()

print("Número de muestras y características de entrenamiento:", X.shape)
print("Número de muestras y características de prueba:", X_test.shape)

"""###visualizar cualquiera de los ECG que contiene el dataset"""

plt.figure(figsize=(15,5))
plt.plot(x, X[0])
plt.xlabel('Time(sec)')
plt.ylabel('Amplitude')
plt.title('ECG Signal - Record 0')
plt.show()

"""###Desarrollo de la arquitectura del modelo"""

n_epochs = 10

"""###Arquitectura Con1d la más utilizada según la literatura para la interpretación de ECG dada su uni-dimensionalidad"""

def get_baseline_model():  #Baseline es una arquitectura en la cual se evaluan diferentes modelos para luego decidir el mejor
    nclass = 1
    inp = Input(shape=(187, 1))
    img_1 = Convolution1D(16, kernel_size=5, activation=activations.relu, padding="valid")(inp)
    img_1 = Convolution1D(16, kernel_size=5, activation=activations.relu, padding="valid")(img_1)
    img_1 = MaxPool1D(pool_size=2)(img_1)
    img_1 = Dropout(rate=0.1)(img_1)
    img_1 = Convolution1D(32, kernel_size=3, activation=activations.relu, padding="valid")(img_1)
    img_1 = Convolution1D(32, kernel_size=3, activation=activations.relu, padding="valid")(img_1)
    img_1 = MaxPool1D(pool_size=2)(img_1)
    img_1 = Dropout(rate=0.1)(img_1)
    img_1 = Convolution1D(32, kernel_size=3, activation=activations.relu, padding="valid")(img_1)
    img_1 = Convolution1D(32, kernel_size=3, activation=activations.relu, padding="valid")(img_1)
    img_1 = MaxPool1D(pool_size=2)(img_1)
    img_1 = Dropout(rate=0.1)(img_1)
    img_1 = Convolution1D(256, kernel_size=3, activation=activations.relu, padding="valid")(img_1)
    img_1 = Convolution1D(256, kernel_size=3, activation=activations.relu, padding="valid")(img_1)
    img_1 = GlobalMaxPool1D()(img_1)
    img_1 = Dropout(rate=0.2)(img_1)

    dense_1 = Dense(64, activation=activations.relu, name="dense_1")(img_1)
    dense_1 = Dense(64, activation=activations.relu, name="dense_2")(dense_1)
    dense_1 = Dense(nclass, activation=activations.sigmoid, name="dense_3_ptbdb")(dense_1)

    model = models.Model(inputs=inp, outputs=dense_1)
    opt = optimizers.Adam(0.001)

    model.compile(optimizer=opt, loss=losses.binary_crossentropy, metrics=['acc'])
    model.summary()
    return model

"""Realizamos el calculo del area bajo la curva, AUROC y AUPRC para evaluar el modelos"""

#Auroc capacidad del modelo para distinguir entre las clases positiva y negativa a través de diferentes umbrales de clasificación
#AUPRC Precisión del modelo a través de diferentes umbrales de clasificación.

model_baseline = get_baseline_model()
file_path = "baseline_ptbdb.h5"
checkpoint = ModelCheckpoint(file_path, monitor='val_acc', verbose=1, save_best_only=True, mode='max')
early = EarlyStopping(monitor="val_acc", mode="max", patience=5, verbose=1)
redonplat = ReduceLROnPlateau(monitor="val_acc", mode="max", patience=3, verbose=2)
callbacks_list = [checkpoint, early, redonplat]  # early

model_baseline.fit(X, Y, epochs=n_epochs, verbose=2, callbacks=callbacks_list, validation_split=0.1)
model_baseline.load_weights(file_path)

pred_test = model_baseline.predict(X_test)
pred_test = (pred_test>0.5).astype(np.int8)

print('Baseline model results')
f1 = f1_score(Y_test, pred_test)
print("Test f1 score : %s "% f1)

acc = accuracy_score(Y_test, pred_test)
print("Test accuracy score : %s "% acc)

# calculate Receiver Operating Characteristics AUC
roc_auc = roc_auc_score(Y_test, pred_test)
print("AUROC score : %s "% roc_auc)

# calculate precision-recall curve
precision, recall, thresholds = precision_recall_curve(Y_test, pred_test)
# calculate precision-recall AUC
prc_auc = auc(recall, precision)
print("AUPRC score : %s "% prc_auc)

baseline_results = [f1, acc, roc_auc, prc_auc]

"""###Callbacks"""

filepath = "/content/drive/MyDrive/dataset/best_weights.hdf5"
checkpoint = ModelCheckpoint(filepath, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')

early_stop = EarlyStopping(monitor='val_accuracy', patience=5, mode='max')
reduce_lr = ReduceLROnPlateau(monitor='val_accuracy', factor=0.1, patience=3, min_lr=0.00001, verbose=1, mode='max')

"""###Compilación y entrenamiento del modelo"""

model = get_baseline_model()
model.summary()
plot_model(model, show_shapes=True, show_layer_names=True, to_file='model.png')

model.compile(optimizer=optimizers.Adam(lr=0.001), loss=losses.binary_crossentropy, metrics=['accuracy'])

history = model.fit(X, Y, epochs=n_epochs, batch_size=16, callbacks=[checkpoint, early_stop, reduce_lr], validation_split=0.1)

"""###Evaluación del modelo"""

model.load_weights(filepath)
pred_test = model.predict(X_test)
pred_test = (pred_test>0.5).astype(np.int8)

accuracy = accuracy_score(Y_test, pred_test)
roc = roc_auc_score(Y_test, pred_test)
f1 = f1_score(Y_test, pred_test)

print("Accuracy on test data: {:.2f}%".format(accuracy*100))
print("ROC AUC on test data: {:.2f}".format(roc))
print("F1-score on test data: {:.2f}".format(f1))

"""###Curva de precisión-recall y ROC"""

precision, recall, thresholds = precision_recall_curve(Y_test, pred_test)
fpr, tpr, thresholds = roc_curve(Y_test, pred_test)

plt.figure(figsize=(12,5))

plt.subplot(1,2,1)
plt.plot(fpr, tpr, lw=2)
plt.plot([0,1],[0,1], c='violet', ls='--')
plt.xlim([-0.05, 1.05])
plt.ylim([-0.05, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC curve')

plt.subplot(1,2,2)
plt.plot(recall, precision, lw=2)
plt.xlim([-0.05, 1.05])
plt.ylim([-0.05, 1.05])
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Precision-recall curve')

plt.tight_layout()
plt.show()

Y_pred = model.predict(X_test)
Y_pred = (Y_pred > 0.5).astype(np.int8)

from sklearn.metrics import confusion_matrix

cm = confusion_matrix(Y_test, Y_pred)

plt.figure(figsize=(6,6))
sns.heatmap(cm, annot=True, fmt=".0f", linewidths=.5, square = True, cmap = 'Blues_r');
plt.ylabel('Actual label');
plt.xlabel('Predicted label');
plt.title('Confusion matrix');
plt.show()

import random

# Seleccionar 5 muestras aleatorias del conjunto de prueba
samples = random.sample(range(X_test.shape[0]), 10)

# Para cada muestra, predecir la clase utilizando el modelo entrenado
for i in samples:
    x_sample = X_test[i]
    true_label = Y_test[i]
    pred_label = model.predict(x_sample[np.newaxis, ...])[0][0] > 0.5

    # Visualizar el ECG junto con la etiqueta verdadera y predicha
    plt.figure(figsize=(10, 4))
    plt.plot(x, x_sample)
    plt.title(f"Sample {i} - True label:{'NORMAL' if true_label==0 else 'ANORMAL'}, Predicted label: {pred_label}")
    plt.xlabel('Time(sec)')
    plt.ylabel('Amplitude')
    plt.show()

# Guardar modelo
model.save('Wall_e_V3_model.h5')

# Cargar modelo
loaded_model = tf.keras.models.load_model('Wall_e_model.h5')

