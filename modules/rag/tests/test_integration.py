"""Exercise real session creation, backend adapter and guarded tutor with RAG chunks."""

import asyncio
from dataclasses import replace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.database.db import Base
from backend.routers.sessions import create_session
from backend.schemas.api_schemas import CreateSessionRequest
from backend.schemas.contracts import ScaffoldingMove
from backend.services.adapters import get_retriever
from backend.services.mocks.mock_analyzer import MockUnderstandingAnalyzer
from backend.services.orchestrator import TutoringOrchestrator
from modules.rag.config import RagSettings, UNIT_IDS
from modules.rag.retriever import CourseRetriever
from modules.rag.tests.fakes import FakeEmbedder
from modules.tutor import SocraticTutor


def test_tutoring_escalation_preserves_course_sources(tmp_path, monkeypatch) -> None:
    import modules.rag.retriever as module

    retriever = CourseRetriever(replace(RagSettings(), index_dir=tmp_path / "index"), FakeEmbedder())
    monkeypatch.setattr(module, "_default_retriever", lambda settings: retriever)
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            session = asyncio.run(create_session(CreateSessionRequest(unit_id=UNIT_IDS[0]), db))
            orchestrator = TutoringOrchestrator(
                db=db, analyzer=MockUnderstandingAnalyzer(),
                retriever=get_retriever(Settings(_env_file=None, USE_MOCK_RAG=False)),
                tutor=SocraticTutor(use_llm=False),
            )
            turns = [asyncio.run(orchestrator.process_turn(session.session_id, "My prompt is inconsistent."))
                     for _ in range(4)]
            assert [t.message.scaffolding_move for t in turns] == [
                ScaffoldingMove.QUESTION, ScaffoldingMove.HINT,
                ScaffoldingMove.HINT, ScaffoldingMove.EXPLANATION,
            ]
            for turn in turns[1:]:
                assert turn.message.citations
                assert all(c.chunk_id.startswith("rag_") for c in turn.message.citations)
                assert all(c.source_title and c.slide_or_section for c in turn.message.citations)
                assert turn.trace.tutor_output.constraints_validated.no_direct_answer_leaked
            assert all(c.excerpt is None for c in turns[1].message.citations)
            assert all(c.excerpt for c in turns[-1].message.citations)
    finally:
        engine.dispose()
