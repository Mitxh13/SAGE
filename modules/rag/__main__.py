"""Standalone index builder and query runner: ``python -m modules.rag``."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

from backend.schemas.contracts import RetrieverInput
from modules.rag.config import RagSettings, UNIT_IDS
from modules.rag.embeddings import get_embedder
from modules.rag.index import build_index
from modules.rag.ingestion import chunk_sections, manifest_sections, repository_sections
from modules.rag.retriever import CourseRetriever, _default_retriever


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SAGE Course Retriever (Jignas)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("index", help="Build the repository corpus, optionally adding course files")
    build.add_argument("--sources", type=Path, help="JSON source manifest")
    build.add_argument("--sources-only", action="store_true", help="Index only the supplied manifest")
    query = subparsers.add_parser("query", help="Return a RetrieverOutput JSON object")
    query.add_argument("query")
    query.add_argument("--unit", choices=UNIT_IDS, required=True)
    query.add_argument("--top-k", type=int, default=2)
    serve = subparsers.add_parser("serve", help="Warm RAG, then start the existing FastAPI backend")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    for command in (build, query, serve):
        command.add_argument("--index-dir", type=Path)
        command.add_argument("--model", help="Embedding model; rebuild after changing it")
    args = parser.parse_args(argv)
    settings = RagSettings()
    if args.index_dir:
        settings = replace(settings, index_dir=args.index_dir.resolve())
    if args.model:
        settings = replace(settings, model_name=args.model)
    try:
        if args.command == "index":
            if args.sources_only and not args.sources:
                parser.error("--sources-only requires --sources")
            sections = [] if args.sources_only else repository_sections()
            if args.sources:
                sections.extend(manifest_sections(args.sources))
            snapshot = build_index(chunk_sections(sections), get_embedder(settings), settings.index_dir)
            result = {"model": snapshot.model_name, "index_dir": str(settings.index_dir),
                      "chunks_per_unit": {u: len(c) for u, c in snapshot.chunks.items()}}
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "query":
            request = RetrieverInput(query=args.query, unit_id=args.unit, top_k=args.top_k)
            result = CourseRetriever(settings).search(request)
            print(result.model_dump_json(indent=2))
        else:
            import uvicorn

            # Keep the same settings/cache key in the existing dict adapter.
            os.environ["RAG_INDEX_DIR"] = str(settings.index_dir)
            os.environ["RAG_EMBEDDING_MODEL"] = settings.model_name
            os.environ["USE_MOCK_RAG"] = "false"
            _default_retriever(settings).warmup()
            from backend.config import get_settings
            get_settings.cache_clear()
            uvicorn.run("backend.main:app", host=args.host, port=args.port)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"Course retriever failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
