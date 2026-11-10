"""Small deterministic semantic vectors; no model download during unit tests."""

import numpy as np


class FakeEmbedder:
    model_name = "test-course-vectors"
    calls = 0

    def encode(self, texts: list[str]) -> np.ndarray:
        self.calls += 1
        vectors = []
        for text in texts:
            text = text.lower()
            vector = [0.01, 0.01, 0.01, 0.0]
            for i, terms in enumerate([
                ("format", "json", "schema", "structured"),
                ("example", "exemplar", "few-shot", "demonstration"),
                ("temperature", "randomness", "sampling", "decoding"),
            ]):
                vector[i] += sum(term in text for term in terms)
            if any(term in text for term in ("football", "weather", "cake")):
                vector = [0.0, 0.0, 0.0, 1.0]
            vectors.append(vector)
        return np.asarray(vectors, dtype=np.float32)
