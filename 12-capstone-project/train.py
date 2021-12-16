import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import roc_auc_score
import xgboost as xgb


# Parameters
n_splits = 5
output_file = "model.bin"


# Read dataset
df = pd.read_csv("bank-additional-full.csv", sep=';')


# Data preprocessing
binary_values = {'no': 0, 'yes': 1}
df['y'] = df['y'].map(binary_values)

del df['loan']
del df['housing']
del df['day_of_week']
del df['marital']
del df['education']
del df['default']


df_train_full, df_test = train_test_split(df, test_size=0.2, random_state=1)
df_train_full = df_train_full.reset_index(drop=True)
df_test = df_test.reset_index(drop=True)


# Model Training
def train(df_train, y_train):
    del df_train["y"]

    dv = DictVectorizer(sparse=False)
    train_dict = df_train.to_dict(orient="records")
    X_train = dv.fit_transform(train_dict)

    features = dv.get_feature_names()
    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=features)

    xgb_params = {"eta": 0.21, "objective": "binary:logistic", "seed": 1}
    model = xgb.train(xgb_params, dtrain, num_boost_round=100)
    return model, dv


def predict(model, dv, df_val, y_val):
    del df_val["y"]

    val_dict = df_val.to_dict(orient="records")
    X_val = dv.fit_transform(val_dict)

    features = dv.get_feature_names()
    dtest = xgb.DMatrix(X_val, label=y_val, feature_names=features)

    y_pred = model.predict(dtest)
    return y_pred


# Validation
kfold = KFold(n_splits=n_splits, shuffle=True, random_state=1)

fold = 0
scores = []
for train_idx, val_idx in kfold.split(df_train_full):
    df_train = df_train_full.iloc[train_idx]
    df_val = df_train_full.iloc[val_idx]

    y_train = df_train["y"].values
    y_val = df_val["y"].values

    model, dv = train(df_train, y_train)
    y_pred = predict(model, dv, df_val, y_val)

    auc = roc_auc_score(y_val, y_pred)
    scores.append(auc)

    print("AUC on fold {} is {}".format(fold, auc))
    fold = fold + 1

print("Validation results: {} +- {}".format(np.mean(scores).round(3), np.std(scores).round(3)))


# Final model Training

model, dv = train(df_train_full, df_train_full["y"].values)
y_pred = predict(model, dv, df_test, df_test["y"].values)


# Save the model
with open(output_file, "wb") as output:
    pickle.dump((model, dv), output)

print("The model is saved to {}".format(output_file))