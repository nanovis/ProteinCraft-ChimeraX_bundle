# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.commands import CmdDesc      # Command description
from chimerax.atomic import AtomsArg            # Collection of atoms argument
from chimerax.core.commands import BoolArg      # Boolean argument
from chimerax.core.commands import ColorArg     # Color argument
from chimerax.core.commands import IntArg       # Integer argument
from chimerax.core.commands import EmptyArg     # Empty argument
from chimerax.core.commands import Or, Bounded  # Argument modifiers
from chimerax.atomic import Structure           # Structure model type
import json                                     # For JSON formatting


# ==========================================================================
# Functions and descriptions for registering using ChimeraX bundle API
# ==========================================================================


def status(session):
    """Display the current status of ProteinCraft."""

    # ``session`` - ``chimerax.core.session.Session`` instance
    
    # Get all open structure models
    mols = session.models.list(type=Structure)
    
    # Create a dictionary with file paths as keys
    mol_dict = {}
    for mol in mols:
        if hasattr(mol, 'filename') and mol.filename:
            mol_dict[mol.filename] = {
                'id': mol.id_string,
                'name': mol.name,
                'display': mol.display
            }
    
    # Convert to JSON and display
    json_output = json.dumps(mol_dict, indent=2)
    session.logger.info(json_output)


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

