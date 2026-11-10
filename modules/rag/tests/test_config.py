"""RAG overrides follow the repository .env convention and OS precedence."""

from modules.rag import config


def test_repo_environment_file_and_process_override(tmp_path, monkeypatch) -> None:
    (tmp_path / ".env").write_text("RAG_EMBEDDING_MODEL=from-file\nRAG_LOCAL_FILES_ONLY=true\n",
                                    encoding="utf-8")
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    monkeypatch.delenv("RAG_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("RAG_LOCAL_FILES_ONLY", raising=False)
    config._dotenv.cache_clear()
    try:
        assert config.RagSettings().model_name == "from-file"
        assert config.RagSettings().local_files_only
        monkeypatch.setenv("RAG_EMBEDDING_MODEL", "from-process")
        assert config.RagSettings().model_name == "from-process"
    finally:
        config._dotenv.cache_clear()
