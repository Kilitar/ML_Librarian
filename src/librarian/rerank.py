"""Pinned, offline pairwise relevance reranker over a bounded candidate union."""
from pathlib import Path
import re

import os
import numpy as np

MODEL_ID = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
REVISION = "1427fd652930e4ba29e8149678df786c240d8825"
CACHE = Path(os.environ.get("ML_LIBRARIAN_CACHE", str(Path(__file__).resolve().parents[2] / ".cache/hf")))
PARAMETERS = re.compile(r"\b(?:C|gamma|alpha|eps|min_samples|max_depth|n_estimators|learning_rate)\b", re.I)


def parameter_queries(query: str) -> list[str]:
    """Evaluate explicitly named parameters separately, without generating answers."""
    parameters = list(dict.fromkeys(match.group().casefold() for match in PARAMETERS.finditer(query)))
    if len(parameters) < 2:
        return []
    return [PARAMETERS.sub(lambda m: m.group() if m.group().casefold() == parameter else "", query)
            for parameter in parameters[:3]]


def candidate_union(semantic_scores: np.ndarray, lexical_scores: np.ndarray,
                    per_retriever: int = 24) -> list[int]:
    semantic = np.argsort(-semantic_scores, kind="stable")[:per_retriever]
    lexical = [int(i) for i in np.argsort(-lexical_scores, kind="stable")
               if lexical_scores[i] > 0][:per_retriever]
    return list(dict.fromkeys([int(i) for i in semantic] + lexical))


def passage_input(document: dict) -> str:
    # Real provenance supplies topic context for fragments that omit their title.
    title = document.get("streamlit_title") or ""
    return f"Source: {document['source_path']}\n{title}\n\n{document['text']}"


def expand_neighbors(documents: list[dict], candidates: list[int], maximum: int = 96) -> list[int]:
    """Recover nearby structural context, without crossing source boundaries."""
    expanded = list(candidates)
    seen = set(expanded)
    for index in candidates:
        for offset in (-1, 1, -2, 2):
            neighbor = index + offset
            if (0 <= neighbor < len(documents) and neighbor not in seen
                    and documents[neighbor]['source_path'] == documents[index]['source_path']):
                expanded.append(neighbor)
                seen.add(neighbor)
                if len(expanded) >= maximum:
                    return expanded
    return expanded


class PassageReranker:
    def __init__(self, *, use_headings=True):
        import torch
        from sentence_transformers import CrossEncoder
        torch.set_num_threads(min(8, torch.get_num_threads()))
        self.model = CrossEncoder(
            MODEL_ID, revision=REVISION, cache_folder=str(CACHE), device="cpu",
            local_files_only=True, trust_remote_code=False, token=False,
            max_length=512, model_kwargs={"use_safetensors": True},
            activation_fn=torch.nn.Sigmoid(),
        )
        self.use_headings = use_headings

    def score_details(self, query: str, documents: list[dict], *, aspects=None, context=None) -> dict[str, np.ndarray]:
        queries = [query] + parameter_queries(query)
        aspect_offset = len(queries)
        queries += aspects or []
        if context:
            queries.append(context)
        values = self.model.predict(
            [(subquery, passage_input(document)) for subquery in queries for document in documents],
            batch_size=8, show_progress_bar=False, convert_to_numpy=True,
        )
        values = np.asarray(values).reshape(-1)
        if len(values) != len(documents) * len(queries) or not np.isfinite(values).all():
            raise ValueError("Invalid passage reranker output")
        matrix = values.reshape(len(queries), len(documents))
        details = {"relevance": matrix.max(axis=0), "whole_query": matrix[0],
                "aspects": matrix[aspect_offset:aspect_offset + len(aspects or [])].T,
                "context": matrix[-1] if context else None}
        if getattr(self, 'use_headings', False) and not (aspects or context or parameter_queries(query)):
            details = self.add_heading_context(query, documents, details)
        return details

    def add_heading_context(self, query, documents, details):
        from heading_context import AdjacentHeadings
        for name in ('whole_query','relevance'):
            values=np.asarray(details[name])
            if not np.isfinite(values).all() or np.any((values<0)|(values>1)):
                raise ValueError('Invalid original model output')
        if not hasattr(self, 'heading_catalog'):
            try:
                self.heading_catalog = AdjacentHeadings()
            except OSError:
                # Context is optional; preserve base reranking if unavailable.
                return details
        eligible = [(i,self.heading_catalog.for_document(d)) for i,d in enumerate(documents)
                    if details['whole_query'][i] < .20]
        eligible = [(i,h) for i,h in eligible if h]
        if not eligible:
            return details
        values = np.asarray(self.model.predict(
            [(query,passage_input({**documents[i], 'text':h['text']+'\n\n'+documents[i]['text']})) for i,h in eligible],
            batch_size=8, show_progress_bar=False, convert_to_numpy=True)).reshape(-1)
        if len(values)!=len(eligible) or not np.isfinite(values).all() or np.any((values<0)|(values>1)):
            raise ValueError('Invalid heading-context model output')
        output={**details,'whole_query':details['whole_query'].copy(),'relevance':details['relevance'].copy(),
                'base_whole_query':details['whole_query'].copy(),'heading_contexts':[None]*len(documents),
                'heading_scores':[None]*len(documents)}
        for (i,heading),value in zip(eligible,values):
            output['heading_contexts'][i]=heading
            output['heading_scores'][i]=float(value)
            output['whole_query'][i]=max(output['whole_query'][i],value)
            output['relevance'][i]=max(output['relevance'][i],value)
        return output

    def scores(self, query: str, documents: list[dict]) -> np.ndarray:
        return self.score_details(query, documents)["relevance"]
