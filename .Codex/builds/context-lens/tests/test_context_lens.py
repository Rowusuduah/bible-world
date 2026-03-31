import pytest

from context_lens import ContextLens, HaystackTemplate, Needle, build_from_config


@pytest.fixture
def simple_needle():
    return Needle(
        label="api key",
        content="The API key is SK-TEST-12345.",
        question="What is the API key?",
        expected_answer="SK-TEST-12345",
        answer_keywords=["SK-TEST-12345"],
    )


@pytest.fixture
def simple_haystack():
    return HaystackTemplate(
        filler_text="This is background documentation text. ",
        target_tokens=200,
        tokens_per_filler=10,
    )


@pytest.fixture
def always_hit_fn():
    def fn(prompt: str) -> str:
        return "The API key is SK-TEST-12345."

    return fn


@pytest.fixture
def always_miss_fn():
    def fn(prompt: str) -> str:
        return "I do not know the answer."

    return fn


class TestNeedle:
    def test_validate_passes_for_valid_needle(self, simple_needle):
        simple_needle.validate()

    def test_validate_rejects_empty_keywords(self):
        needle = Needle(
            content="fact",
            question="what?",
            expected_answer="fact",
            answer_keywords=[],
        )
        with pytest.raises(ValueError, match="answer_keywords"):
            needle.validate()


class TestHaystackTemplate:
    def test_build_inserts_needle_at_start(self, simple_haystack, simple_needle):
        result = simple_haystack.build(simple_needle.content, 0.0)
        assert simple_needle.content in result

    def test_build_inserts_needle_at_end(self, simple_haystack, simple_needle):
        result = simple_haystack.build(simple_needle.content, 1.0)
        assert simple_needle.content in result

    def test_build_places_end_needle_after_filler(self, simple_needle):
        haystack = HaystackTemplate(
            filler_text="ABC ",
            target_tokens=400,
            tokens_per_filler=4,
        )
        result = haystack.build(simple_needle.content, 1.0)
        needle_pos = result.index(simple_needle.content)
        assert needle_pos > result.index("ABC ")

    def test_build_rejects_invalid_position(self, simple_haystack, simple_needle):
        with pytest.raises(ValueError, match="position_fraction"):
            simple_haystack.build(simple_needle.content, 1.1)


class TestContextLens:
    def test_audit_reliable_when_model_always_hits(
        self, simple_needle, simple_haystack, always_hit_fn, tmp_path
    ):
        lens = ContextLens(
            model_fn=always_hit_fn,
            model_name="test-model",
            db_path=str(tmp_path / "context_lens.db"),
        )
        result = lens.audit(simple_needle, simple_haystack, positions=5, verbose=False)

        assert result.verdict == "RELIABLE"
        assert result.retrieval_score == 1.0
        assert result.timestamp.endswith("Z")

    def test_audit_unreliable_when_model_always_misses(
        self, simple_needle, simple_haystack, always_miss_fn, tmp_path
    ):
        lens = ContextLens(
            model_fn=always_miss_fn,
            model_name="test-model",
            db_path=str(tmp_path / "context_lens.db"),
        )
        result = lens.audit(simple_needle, simple_haystack, positions=5, verbose=False)

        assert result.verdict == "UNRELIABLE"
        assert result.retrieval_score == 0.0
        assert len(result.fault_zones) == 5

    def test_history_returns_saved_audits(
        self, simple_needle, simple_haystack, always_hit_fn, tmp_path
    ):
        db_path = str(tmp_path / "context_lens.db")
        lens = ContextLens(model_fn=always_hit_fn, db_path=db_path)
        lens.audit(simple_needle, simple_haystack, positions=3, verbose=False)

        history = lens.history(limit=5)
        assert len(history) == 1
        assert history[0]["needle_label"] == "api key"

    def test_ci_gate_fails_for_unreliable_heatmap(
        self, simple_needle, simple_haystack, always_miss_fn, tmp_path
    ):
        lens = ContextLens(
            model_fn=always_miss_fn,
            db_path=str(tmp_path / "context_lens.db"),
        )
        heatmap = lens.audit(simple_needle, simple_haystack, positions=4, verbose=False)
        passed, message = lens.ci_gate([heatmap], min_score=0.8, fail_on_unreliable=True)

        assert passed is False
        assert "UNRELIABLE" in message

    def test_summary_report_aggregates_multiple_heatmaps(
        self, simple_needle, simple_haystack, always_hit_fn, always_miss_fn, tmp_path
    ):
        db_path = str(tmp_path / "context_lens.db")
        reliable_lens = ContextLens(model_fn=always_hit_fn, db_path=db_path)
        unreliable_lens = ContextLens(model_fn=always_miss_fn, db_path=db_path)

        reliable = reliable_lens.audit(simple_needle, simple_haystack, positions=3, verbose=False)
        unreliable = unreliable_lens.audit(simple_needle, simple_haystack, positions=3, verbose=False)

        summary = reliable_lens.summary_report([reliable, unreliable])
        assert summary["needles_tested"] == 2
        assert summary["any_unreliable"] is True
        assert summary["overall_verdict"] == "UNRELIABLE"


class TestBuildFromConfig:
    def test_build_from_config_returns_expected_objects(self):
        config = {
            "model_name": "demo-model",
            "positions": 6,
            "haystack": {
                "filler_text": "background",
                "target_tokens": 120,
                "tokens_per_filler": 12,
            },
            "needles": [
                {
                    "label": "api key",
                    "content": "The API key is SK-TEST-12345.",
                    "question": "What is the API key?",
                    "expected_answer": "SK-TEST-12345",
                    "answer_keywords": ["SK-TEST-12345"],
                }
            ],
        }

        lens, needles, haystack, positions = build_from_config(config, lambda prompt: "")

        assert lens.model_name == "demo-model"
        assert len(needles) == 1
        assert haystack.filler_text == "background"
        assert positions == 6
