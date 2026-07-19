"""Import-smoke for the Phase C Operations view (advisory UI)."""
import importlib

import ui.views.operations_view as operations_view


def test_operations_view_imports():
    assert hasattr(operations_view, "OperationsView")
    assert hasattr(operations_view, "build")


def test_operations_view_build_is_callable():
    assert callable(operations_view.build)


def test_operations_sections_render_without_backend():
    # The view's section builders must degrade gracefully when subsystems are
    # partially available. We only assert they return strings.
    view = operations_view.OperationsView.__new__(operations_view.OperationsView)
    assert isinstance(view._active_goal(), str)
    assert isinstance(view._agent_state(), str)
    assert isinstance(view._blockers(), str)
    assert isinstance(view._providers(), str)


def test_operations_uses_read_only_surfaces():
    # Confirm the module never imports the Governor mutation surface.
    src = importlib.util.find_spec("ui.views.operations_view").loader.get_data(
        importlib.util.find_spec("ui.views.operations_view").origin
    ).decode("utf-8")
    assert "request_level_change" not in src
    assert "emergency_stop" not in src