# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.commands import CmdDesc      # Command description
from chimerax.atomic import AtomsArg            # Collection of atoms argument
from chimerax.core.commands import BoolArg      # Boolean argument
from chimerax.core.commands import ColorArg     # Color argument
from chimerax.core.commands import IntArg       # Integer argument
from chimerax.core.commands import EmptyArg     # Empty argument
from chimerax.core.commands import StringArg    # String argument
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


def sync(session, jsonString=None):
    """Synchronize with ProteinCraft."""

    # ``session`` - ``chimerax.core.session.Session`` instance
    # ``jsonString`` - string, JSON string containing model display states
    
    if jsonString is None:
        session.logger.warning("No JSON string provided")
        return
    
    try:
        # Parse the JSON string
        display_states = json.loads(jsonString)
        
        # Get all open structure models
        mols = session.models.list(type=Structure)
        
        # Update display state for each model
        for mol in mols:
            if hasattr(mol, 'filename') and mol.filename:
                if mol.filename in display_states:
                    mol.display = display_states[mol.filename]['display']
        
        session.logger.info("Successfully updated model display states")
        
    except json.JSONDecodeError:
        session.logger.error("Invalid JSON string provided")
    except Exception as e:
        session.logger.error(f"Error updating model display states: {str(e)}")


sync_desc = CmdDesc(keyword=[("jsonString", StringArg)])

# CmdDesc contains the command description.
# For the "sync" command, we have one optional argument:
#   ``jsonString`` - string (optional), default: None

