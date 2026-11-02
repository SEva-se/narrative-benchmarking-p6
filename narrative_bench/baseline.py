"""CPU-only multilabel TF-IDF centroid baseline with a development-set threshold."""
from collections import Counter
import math
import re


def tokenize(text):
    return re.findall(r"\b\w\w+\b", text.casefold(), flags=re.UNICODE)


def unit(vector):
    size = math.sqrt(sum(v * v for v in vector.values()))
    return {k: v / size for k, v in vector.items()} if size else {}


def dot(a, b):
    return sum(v * b.get(k, 0) for k, v in a.items())


class TfidfCentroid:
    def fit(self, rows, label_ids):
        if not rows or any(r["split"] != "train" or r.get("labels") is None for r in rows):
            raise ValueError("Baseline fit requires labeled training rows")
        self.label_ids = sorted(label_ids)
        df = Counter()
        for r in rows:
            df.update(set(tokenize(r["text"])))
        self.idf = {t: math.log((1 + len(rows)) / (1 + n)) + 1 for t, n in df.items()}
        sums = {k: Counter() for k in self.label_ids}
        for r in rows:
            vec = self.vector(r["text"])
            for label in r["labels"]:
                sums[label].update(vec)
        self.centroids = {k: unit(dict(v)) for k, v in sums.items()}
        return self

    def vector(self, text):
        tf = Counter(tokenize(text))
        return unit({k: (1 + math.log(v)) * self.idf[k] for k, v in tf.items() if k in self.idf})

    def predict(self, text, threshold):
        vec = self.vector(text)
        return [k for k in self.label_ids if self.centroids[k] and dot(vec, self.centroids[k]) >= threshold]

    def tune(self, dev):
        from .metrics import classification
        if not dev or any(r["split"] != "dev" or r.get("labels") is None for r in dev):
            raise ValueError("Threshold selection requires labeled dev records")
        choices = []
        for threshold in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.75]:
            score = classification([r["labels"] for r in dev], [self.predict(r["text"], threshold) for r in dev], self.label_ids)
            choices.append((score["macro_f1_present_gold"], threshold))
        return max(choices)[1]
