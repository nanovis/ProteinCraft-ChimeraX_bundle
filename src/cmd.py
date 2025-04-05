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
from chimerax.core.commands import run

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
        
        # First, set display to False for all currently open models
        for mol in mols:
            if hasattr(mol, 'filename') and mol.filename:
                mol.display = False
        
        # Process files that should be displayed
        for filepath, state in display_states.items():
            if state.get('display', False):  # Only process if display is True
                # Check if file is already open
                file_open = False
                for mol in mols:
                    if hasattr(mol, 'filename') and mol.filename == filepath:
                        mol.display = True
                        # Show sequence viewer for all chains
                        run(session, f"sequence chain #{mol.id_string}/A")
                        run(session, f"sequence chain #{mol.id_string}/B")

                        file_open = True
                        break
                
                # If file is not open, open it
                if not file_open:
                    try:
                        mol = run(session, f"open {filepath}")
                        mol.display = True
                        # Show sequence viewer for all chains
                        run(session, f"sequence chain #{mol.id_string}/A")
                        run(session, f"sequence chain #{mol.id_string}/B")
                    except Exception as e:
                        session.logger.error(f"Error opening file {filepath}: {str(e)}")
        
        session.logger.info("Successfully updated model display states")
        
    except json.JSONDecodeError:
        session.logger.error("Invalid JSON string provided")
    except Exception as e:
        session.logger.error(f"Error updating model display states: {str(e)}")


sync_desc = CmdDesc(keyword=[("jsonString", StringArg)])

# CmdDesc contains the command description.
# For the "sync" command, we have one optional argument:
#   ``jsonString`` - string (optional), default: None

