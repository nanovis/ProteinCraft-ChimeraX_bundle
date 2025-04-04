# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.commands import CmdDesc      # Command description
from chimerax.atomic import AtomsArg            # Collection of atoms argument
from chimerax.core.commands import BoolArg      # Boolean argument
from chimerax.core.commands import ColorArg     # Color argument
from chimerax.core.commands import IntArg       # Integer argument
from chimerax.core.commands import EmptyArg     # Empty argument
from chimerax.core.commands import Or, Bounded  # Argument modifiers


# ==========================================================================
# Functions and descriptions for registering using ChimeraX bundle API
# ==========================================================================


def status(session):
    """Display the current status of ProteinCraft."""

    # ``session`` - ``chimerax.core.session.Session`` instance
    
    # For now, just print the command itself
    session.logger.info("proteincraft status")


status_desc = CmdDesc()

# CmdDesc contains the command description.
# For the "status" command, we don't have any required or optional arguments for now.


def sync(session, force=False):
    """Synchronize with ProteinCraft."""

    # ``session`` - ``chimerax.core.session.Session`` instance
    # ``force``   - boolean, whether to force synchronization
    
    # For now, just print the command itself
    session.logger.info("proteincraft sync force=%s" % force)


sync_desc = CmdDesc(optional=[("force", BoolArg)])

# CmdDesc contains the command description.
# For the "sync" command, we have one optional argument:
#   ``force`` - boolean (optional), default: False

