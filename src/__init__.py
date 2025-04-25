# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.toolshed import BundleAPI
import urllib.request, urllib.parse
import json
from chimerax.core import models, selection
import chimerax.atomic as atomic


def initialize(session):
    """Initialize the ProteinCraft bundle."""
    session.logger.info("ProteinCraft: initialize")
    # Wait for the main UI to be ready before adding handlers
    if session.ui.is_gui:
        session.ui.triggers.add_handler('ready', lambda t, d: _register_handlers(session))
    else:
        # For command-line interface, register handlers immediately
        _register_handlers(session)

def _register_handlers(session):
    """Register event handlers for the session."""
    ts = session.triggers
    # 1) Selection changes
    ts.add_handler(selection.SELECTION_CHANGED, lambda t, d: _post_event(session, "selection_changed", {}))
    # 2) Model position changes (e.g. moving or rotating models)
    ts.add_handler(models.MODEL_POSITION_CHANGED, lambda t, model: _post_event(session, "model_moved", {"model": model.id}))
    # 3) Per-frame draw (use this to detect camera/view changes)
    ts.add_handler('frame drawn', lambda t, loop: _post_camera_state(session))
    # 4) Atomic attribute changes (e.g. display on/off)
    at = atomic.get_triggers(session)
    at.add_handler('changes done', lambda t, changes: _post_display_changes(session, changes))

def _post_event(session, event_type, data):
    """Post an event with the given type and data."""
    payload = json.dumps({"event": event_type, "data": data}).encode('utf-8')
    session.logger.info("ProteinCraft: _post_event: " + payload.decode('utf-8'))

def _post_camera_state(session):
    """Post the current camera state."""
    view = session.main_view  # a chimerax.graphics.view.View instance
    cam = view.camera
    # Convert Place object to serializable format
    pos = cam.position
    state = {
        "position": {
            "origin": pos.origin().tolist(),
            "axes": [pos.axes()[i].tolist() for i in range(3)]
        }
        # "fov": cam.field_of_view
    }
    _post_event(session, "camera_changed", state)

def _post_display_changes(session, changes):
    """Post display changes for atomic structures."""
    if changes is None:
        return
    # look for "display" attr changes on structures
    for struct in changes.modified_atomic_structures():
        if 'display changed' in changes.reasons(struct):
            _post_event(session, "display_toggled", {"structure": struct.id, "display": struct.display})

class _ProteinCraftAPI(BundleAPI):
    """API for the ProteinCraft bundle."""

    api_version = 1  # Use BundleInfo and CommandInfo instances

    @staticmethod
    def register_command(bi, ci, logger):
        """Register a command with ChimeraX."""

        # bi is an instance of chimerax.core.toolshed.BundleInfo
        # ci is an instance of chimerax.core.toolshed.CommandInfo
        # logger is an instance of chimerax.core.logger.Logger

        # This method is called once for each command listed
        # in bundle_info.xml.

        from . import cmd
        if ci.name == "proteincraft status":
            func = cmd.status
            desc = cmd.status_desc
        elif ci.name == "proteincraft sync":
            func = cmd.sync
            desc = cmd.sync_desc
        elif ci.name == "proteincraft sync_bonds":
            func = cmd.sync_bonds
            desc = cmd.sync_bonds_desc
        elif ci.name == "proteincraft printJson":
            func = cmd.printJson
            desc = cmd.printJson_desc
        elif ci.name == "proteincraft bondDetail":
            func = cmd.bondDetail
            desc = cmd.bondDetail_desc
        else:
            raise ValueError(f"trying to register unknown command: {ci.name}")

        if desc.synopsis is None:
            desc.synopsis = ci.synopsis

        from chimerax.core.commands import register
        register(ci.name, desc, func)

    @staticmethod
    def initialize(session, bundle_info):
        """Initialize the bundle when it is loaded."""
        initialize(session)

    @staticmethod
    def finish(session, bundle_info):
        """Clean up when the bundle is unloaded."""
        session.logger.info("ProteinCraft: finish unloading")

# Create the bundle_api object that ChimeraX expects
bundle_api = _ProteinCraftAPI()
