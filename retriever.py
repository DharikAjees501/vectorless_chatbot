from rank_bm25 import BM25Okapi


class VectorlessRetriever:
    def __init__(self):
        self.pages = []
        self.bm25 = None
        self.tokenized_pages = []

    def build_index(self, pages):
        self.pages = pages

        self.tokenized_pages = [
            page["text"].lower().split()
            for page in pages
        ]

        self.bm25 = BM25Okapi(self.tokenized_pages)

    def search(self, query, top_k=3, selected_files=None):

        if not self.bm25:
            return []

        tokenized_query = query.lower().split()

        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )

        results = []

        for idx, score in ranked:

            page = self.pages[idx]

            # Filter by selected PDFs
            if selected_files:
                if page["file_name"] not in selected_files:
                    continue

            if score > 0:
                results.append(page)

            if len(results) >= top_k:
                break

        return results