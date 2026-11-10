# Course Retriever design and research

Owner: Paturu Naga Jignas (PES2UG24AM110).

## Repository requirements

`docs/CONTEXT.md` §4 and §5.3 require course evidence with traceable sources.
Section 8 supplies the initial Unit 1–3 concept summaries. `data/units/`
supplies topic expectations, so related content can retain its topic identity.
`docs/ARCHITECTURE.md` requires a local index, the frozen RetrieverInput /
RetrieverOutput contract and a total turn latency below 10 seconds.

Only course concepts enter the default student-facing index. Research summaries
inform this design; architecture instructions and learner-state formulas do not
become course facts. Sources remain labelled as repository summaries or taxonomy,
with section references. No lecture slide provenance is invented.

## Research applied

| Source | Evidence consulted | Application in SAGE retrieval |
|---|---|---|
| [Jain et al., KITE (2026)](https://arxiv.org/html/2605.12988v1), §3.1–3.3 | Full paper: section-aware chunks, normalized embeddings, FAISS and a dense/lexical retrieval combination | Preserve section/page boundaries; use normalized local vectors and a small lexical contribution for exact course terminology. KITE's larger cross-encoder/multimodal pipeline is not required for three units. |
| [Dong et al., KG-RAG (2025)](https://arxiv.org/abs/2311.17696v7) | Author abstract and the summary in CONTEXT.md §5.2 | Preserve unit and topic relationships in metadata. This implementation uses topic metadata, not a knowledge graph; it does not claim to reproduce KG-RAG. |
| [Vu-Minh et al., SmartStudy (HICSS 2026)](https://ssrn.com/abstract=5607971) | Author abstract and CONTEXT.md §5.2; full text was not accessible during implementation | Use an explicit course corpus and inspect retrieval relevance separately from tutor generation. |
| [Hu et al., Socratic Playground (2025)](https://arxiv.org/html/2501.06682v1) | Full paper and CONTEXT.md §6 | Use the existing topic expectations as retrieval context; leave learner assessment and stage selection to their owning modules. |
| [Thonge & Thakkar (2026)](https://doi.org/10.1145/3803400.3809368) | CONTEXT.md §7; publisher full text was inaccessible | Preserve the existing separation of retrieval, state tracking and guarded tutor generation. |

These are implementation choices motivated by the papers, not replications of
their reported experiments. The retrieval evaluation measures this corpus only;
it does not establish student learning outcomes or validate the paper summaries.

## Stack decision

Use FAISS `IndexFlatIP` with normalized embeddings from the local
`sentence-transformers/all-MiniLM-L6-v2` model. Exact search is appropriate for a
small three-unit corpus and requires no server. Unit-specific indexes enforce
the unit filter before ranking. JSON stores provenance and topic metadata.

The encoder runs on CPU, is loaded once per process, and requires no hosted API
key. Its first use downloads model weights; later runs can use the local cache.
Chunks are kept short to respect the model's 256-wordpiece input limit.
Scores are ranking scores in [0, 1], not probabilities of factual correctness.
The default model revision is pinned and included in the saved index identity,
so a later upstream model update cannot silently change its embedding space.

Primary implementation references:
- [FAISS index selection](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)
- [Sentence Transformers semantic search](https://sbert.net/examples/sentence_transformer/applications/semantic-search/)
- [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

## Task checklist

- [x] Review repository ownership, contracts, research and stack choices.
- [x] Ingest Markdown, taxonomy JSON, PDF slides and PowerPoint slides with provenance.
- [x] Chunk and embed course material and persist a validated vector index.
- [x] Implement filtered retrieval, async service and existing adapter compatibility.
- [x] Provide standalone indexing/query commands and backend integration checks.
- [x] Evaluate retrieval over all three units and document reproducible use.
