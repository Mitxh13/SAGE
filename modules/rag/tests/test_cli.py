"""Standalone indexing/query commands, including failure messages."""

import json

from modules.rag.__main__ import main
from modules.rag.config import UNIT_IDS
from modules.rag.tests.fakes import FakeEmbedder


def test_index_and_query_commands_use_the_same_persisted_corpus(tmp_path, monkeypatch, capsys) -> None:
    import modules.rag.__main__ as cli
    import modules.rag.retriever as retriever_module

    monkeypatch.setattr(cli, "get_embedder", lambda settings: FakeEmbedder())
    monkeypatch.setattr(retriever_module, "get_embedder", lambda settings: FakeEmbedder())
    assert main(["index", "--index-dir", str(tmp_path)]) == 0
    built = json.loads(capsys.readouterr().out)
    assert set(built["chunks_per_unit"]) == set(UNIT_IDS)
    assert main(["query", "JSON format", "--unit", UNIT_IDS[0], "--top-k", "1",
                 "--index-dir", str(tmp_path)]) == 0
    response = json.loads(capsys.readouterr().out)
    assert len(response["chunks"]) == 1
    assert response["chunks"][0]["unit_id"] == UNIT_IDS[0]
    assert main(["query", "JSON format", "--unit", UNIT_IDS[0], "--top-k", "0"]) == 1
    assert "failed" in capsys.readouterr().err
