import numpy as np
import multiprocessing
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn import utils
from sklearn.feature_extraction.text import TfidfVectorizer
from gensim.models import Doc2Vec
from gensim.models.doc2vec import TaggedDocument
from abc import ABC, abstractmethod


class TextEncoder(ABC):

    def __init__(self, language="english", encoding_length=50):
        self.language = language
        self.encoding_length = encoding_length
        super().__init__()

    @abstractmethod
    def fit(self, docs):
        pass

    @abstractmethod
    def transform(self, docs):
        pass


class BoNGTextEncoder(TextEncoder):

    def __init__(self, language="english", encoding_length=50, n=2):
        self.n = n
        self.vectorizer = None
        super().__init__(language=language, encoding_length=encoding_length)

    def fit(self, docs):
        self.vectorizer = TfidfVectorizer(ngram_range=(self.n, self.n), max_features=self.encoding_length, analyzer='word', norm="l2")
        return self.vectorizer.fit(preprocess_docs(docs, language=self.language))

    def transform(self, docs):
        self.vectorizer.transform(preprocess_docs(docs, language=self.language))


class PVTextEncoder(TextEncoder):

    def __init__(self,  language="english", encoding_length=50, epochs=10, min_count=2):
        self.epochs = epochs
        self.min_count = min_count
        self.workers = multiprocessing.cpu_count()
        self.model = None
        super().__init__(language=language, encoding_length=encoding_length)

    def fit(self, docs):
        docs = preprocess_docs(docs, language=self.language)

        tagged_docs = [TaggedDocument(words=word_tokenize(doc), tags=[i]) for i, doc in enumerate(docs)]

        self.model = Doc2Vec(dm=0, vector_size=self.encoding_length, negative=5, hs=0, min_count=self.min_count, sample=0, workers=self.workers)
        self.model.build_vocab(tagged_docs)

        self.model.train(utils.shuffle(tagged_docs), total_examples=len(tagged_docs), epochs=self.epochs)

    def transform(self, docs):
        docs = preprocess_docs(docs, language=self.language)
        return np.array([self.model.infer_vector(word_tokenize(doc)) for doc in docs])


def preprocess_docs(docs, language="english"):
    nltk.download("wordnet")
    nltk.download("punkt")
    stop_words = set(stopwords.words(language))
    lemmatizer = WordNetLemmatizer()
    docs_preprocessed = []
    for doc in docs:
        doc = doc.lower()
        words = word_tokenize(doc)
        docs_preprocessed.append(" ".join([lemmatizer.lemmatize(word) for word in words if word not in stop_words and word.isalpha()]))
    return docs_preprocessed
