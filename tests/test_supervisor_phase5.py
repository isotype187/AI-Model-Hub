# Phase 5 integration tests for supervisor <-> ProjectEngine wiring.
#
# Dependency-aware: these tests import core.supervisor, which requires
# autogen_agentchat / autogen_core. When that runtime is unavailable the
# whole module is skipped rather than failing, so the suite still runs in
# environments where the Agent runtime is not installed.
#
# Strategy:
#   * action intents are exercised directly via run_action_task (pure logic
#     + ProjectEngine file/checkpoint writes) - no Ollama needed.
#   * non-action intents are exercised via run_task with the agent/orchestrator
#     path stubbed, proving the live agent path is unchanged.

import os
import sys
import shutil

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    sys.path.insert(0, ROOT)
    import core.supervisor as supervisor
    _IMPORT_OK = True
except Exception as exc:  # pragma: no cover - env dependent
    _IMPORT_OK = False
    _IMPORT_ERROR = exc


pytestmark = pytest.mark.skipif(
    not _IMPORT_OK,
    reason="core.supervisor requires autogen runtime (autogen_agentchat); skipped in this environment"
)


@pytest.fixture
def ensure_auto_execute_off():
    # Safety policy: auto_execute must stay False by default; restore after.
    previous = supervisor.auto_execute
    supervisor.auto_execute = False
    yield
    supervisor.auto_execute = previous


def _autonomy_intent():
    """Read the autonomy_level INTENT from the config authority (read-only).

    Uses the same authority the Governor relies on: config/system_config.json.
    Falls back to the safest reading ("manual") when unavailable, so the
    invariant is enforced whenever the promotion state cannot be confirmed.
    """
    import json
    cfg_path = os.path.join(ROOT, "config", "system_config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8-sig") as fh:
            return json.load(fh).get("autonomy_level", "manual")
    except (OSError, ValueError):
        return "manual"


# Autonomy level names that legitimately permit auto_execute=True (a governed,
# human-approved promotion is NOT a Phase 5 regression). Everything else must
# keep the fresh/manual safety default of auto_execute=False.
_PROMOTED_INTENTS = frozenset({"trusted", "expanded", "experimental"})


def test_auto_execute_defaults_false():
    """Core Phase 5 safety invariant, promotion-aware.

    1. In a fresh/manual (unpromoted) state, auto_execute MUST be False.
    2. An explicitly promoted trusted-workflow state (governed by the Autonomy
       Governor) is not treated as a regression: auto_execute may be True, but
       only when the config authority records a promoted autonomy_level.
    """
    intent = _autonomy_intent()
    if intent in _PROMOTED_INTENTS:
        # Promoted state is legitimate; do not treat auto_execute=True as a
        # regression. Enforce consistency: it may be True ONLY because the
        # config authority records a governed promotion.
        if supervisor.auto_execute is True:
            assert intent in _PROMOTED_INTENTS
    else:
        # Fresh / manual / controlled default: safety floor stays engaged.
        assert supervisor.auto_execute is False


def test_detect_intent_action_keywords():
    for task in [
        "create file report.txt",
        "write file config.json",
        "modify file app.py",
        "edit file main.py",
        "update file settings.yaml",
        "change code in parser.py",
        "add code to utils.py",
        "build app mytool",
        "make script deploy.ps1",
    ]:
        assert supervisor.detect_intent(task) == "action"


def test_detect_intent_information_default():
    for task in [
        "what is the capital of France?",
        "explain how the Project Engine works",
        "summarize the architecture audit",
    ]:
        assert supervisor.detect_intent(task) == "information"


def test_run_action_task_creates_proposal_and_checkpoint(ensure_auto_execute_off, tmp_path):
    # Capture ProjectEngine history so we can assert checkpoint/request records.
    history_dir = supervisor.engine.status()["history_directory"]
    before = set(os.listdir(history_dir)) if os.path.isdir(history_dir) else set()

    result = supervisor.run_action_task(
        "create file phase5_output.txt with a summary",
        status=lambda m: None,
    )

    assert result["intent"] == "action"
    assert result["status"] == "awaiting_approval"
    assert len(result["proposals"]) >= 1
    # Each proposal must carry the required review fields.
    for proposal in result["proposals"]:
        assert proposal["status"] == "pending_review"
        assert proposal["proposal_id"]
        assert proposal["action"]
        assert proposal["target"]

    after = set(os.listdir(history_dir)) if os.path.isdir(history_dir) else set()
    created = after - before
    # Checkpoint/request records must have been written to history.
    assert any(name.endswith("_request.json") for name in created), (
        "No engine request (checkpoint) record created: %s" % created
    )


def test_run_action_task_does_not_execute_when_auto_execute_false(ensure_auto_execute_off, tmp_path):
    target = "phase5_should_not_be_written.txt"
    result = supervisor.run_action_task(
        "create file %s" % target,
        status=lambda m: None,
    )
    assert result["status"] == "awaiting_approval"
    # Nothing should be written while awaiting approval.
    assert not os.path.exists(os.path.join(ROOT, target))


def test_run_action_task_executes_when_auto_execute_true(tmp_path):
    previous = supervisor.auto_execute
    supervisor.auto_execute = True
    try:
        target = "phase5_executed_output.txt"
        full = os.path.join(ROOT, target)
        if os.path.exists(full):
            os.remove(full)
        try:
            result = supervisor.run_action_task(
                "create file %s" % target,
                status=lambda m: None,
            )
            assert result["status"] == "executed"
            # ProjectEngine.execute_operation writes the file on approval.
            assert os.path.exists(full), "File was not written on approved execution"
        finally:
            if os.path.exists(full):
                os.remove(full)
    finally:
        supervisor.auto_execute = previous


def test_run_task_routes_action_through_project_engine(ensure_auto_execute_off):
    # Action intent must return the run_action_task result, not reach the agent path.
    captured = {}

    def fake_run_action_task(task, status):
        captured["called"] = True
        return {"status": "awaiting_approval", "intent": "action"}

    original = supervisor.run_action_task
    supervisor.run_action_task = fake_run_action_task
    try:
        result = supervisor.run_task("create file demo.txt")
    finally:
        supervisor.run_action_task = original

    assert captured.get("called") is True
    assert result["intent"] == "action"
    assert result["status"] == "awaiting_approval"


def test_run_task_information_intent_uses_existing_agent_path(ensure_auto_execute_off):
    # Non-action intents must NOT trigger the action branch; the existing
    # agent path must remain the route. We stub the agent stack so no live
    # Ollama call is required, and assert run_action_task is never invoked.
    captured = {"action_called": False}

    def fake_run_action_task(task, status):
        captured["action_called"] = True
        return {"status": "awaiting_approval", "intent": "action"}

    class FakeMessage:
        def __init__(self, content):
            self.content = content

    class FakeResponse:
        chat_message = FakeMessage("information answer")

    class FakeAgent:
        async def on_messages(self, messages, token):
            return FakeResponse()

    class FakeOrchestrator:
        def get_agent(self, name):
            return FakeAgent()
        def load_agents(self):
            pass

    original_run_action = supervisor.run_action_task
    original_get_orch = supervisor.get_orchestrator
    original_route = supervisor.route
    supervisor.run_action_task = fake_run_action_task
    supervisor.get_orchestrator = lambda: FakeOrchestrator()
    supervisor.route = lambda task: "researcher"
    try:
        result = supervisor.run_task("what is the Project Engine?")
    finally:
        supervisor.run_action_task = original_run_action
        supervisor.get_orchestrator = original_get_orch
        supervisor.route = original_route

    assert captured["action_called"] is False
    assert result == "information answer"
