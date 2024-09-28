# -*- coding: utf-8 -*-

import nltk
import string
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer, PorterStemmer
from sqlalchemy import create_engine

engine = create_engine('sqlite:///messages_categories.db')
df = pd.read_sql_table('messages_categories', con=engine)

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

# Initialize stop words, lemmatizer, and stemmer
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()

def preprocess_message(message):
    message = message.lower()

    # Tokenize the message
    tokens = word_tokenize(message)

    # Remove punctuation and non-alphabetic characters
    tokens = [word for word in tokens if word.isalpha()]

    # Remove stop words
    tokens = [word for word in tokens if word not in stop_words]

    # Lemmatization and Stemming
    cleaned_tokens = [stemmer.stem(lemmatizer.lemmatize(word)) for word in tokens]

    # Rejoin tokens
    cleaned_message = ' '.join(cleaned_tokens)

    return cleaned_message

X = df['message']
y = df.iloc[:, 4:]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Build the machine learning pipeline with XGBoost as the base estimator
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(tokenizer=preprocess_message)),  # Vectorizer with custom preprocessing
    ('clf', MultiOutputClassifier(XGBClassifier(use_label_encoder=False, eval_metric='mlogloss')))  # Multi-output classifier
])

# Define the parameter grid for hyperparameter tuning
param_grid = {
    'clf__estimator__n_estimators': [50, 100],
    'clf__estimator__max_depth': [3, 5, 7],
    'clf__estimator__learning_rate': [0.01, 0.1, 0.2],
}

grid_search = GridSearchCV(pipeline, param_grid, cv=5, scoring='f1_micro', n_jobs=-1)
grid_search.fit(X_train, y_train)

best_pipeline = grid_search.best_estimator_

y_pred = best_pipeline.predict(X_test)

for i, col in enumerate(y.columns):
    print(f'Classification report for {col}:')
    print(classification_report(y_test.iloc[:, i], y_pred[:, i]))
    print("\n")
print("Best parameters found: ", grid_search.best_params_)
