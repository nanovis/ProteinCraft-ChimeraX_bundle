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
    """Synchronize with ProteinCraft using a JSON string."""

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
                        file_open = True
                        break
                
                # If file is not open, open it
                if not file_open:
                    try:
                        mol = run(session, f"open {filepath}")[0]
                        mol.display = True
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


def sync_bonds(session, jsonString=None):
    """Synchronize bonds with ChimeraX using the pbond command."""

    if jsonString is None:
        session.logger.warning("No JSON string provided for bond synchronization")
        return

    try:
        # Parse the JSON string
        bond_data = json.loads(jsonString)

        # Iterate over each bond and create a pseudobond
        for bond in bond_data:
            chain1 = bond.get('chain1')
            pos1 = bond.get('pos1')
            chain2 = bond.get('chain2')
            pos2 = bond.get('pos2')
            atom1 = bond.get('atom1')
            atom2 = bond.get('atom2')

            if all([chain1, pos1, chain2, pos2, atom1, atom2]):
                # Format atom specifications for ChimeraX
                residue1 = f"#1/{chain1}:{pos1}"  # Using CA atom for residue
                residue2 = f"#1/{chain2}:{pos2}"  # Using CA atom for residue
                # Show atoms
                run(session, f"show {residue1} atoms")
                run(session, f"show {residue2} atoms")
                # Construct the pbond command
                pbond_command = f"pbond {residue1}@{atom1} {residue2}@{atom2} color gold radius 0.2"
                run(session, pbond_command)
                # Color the atoms
                run(session, f"color {residue1} red")
                run(session, f"color {residue2} red")

        session.logger.info("Successfully synchronized bonds with ChimeraX")

    except json.JSONDecodeError:
        session.logger.error("Invalid JSON string provided for bond synchronization")
    except Exception as e:
        session.logger.error(f"Error synchronizing bonds: {str(e)}")

sync_bonds_desc = CmdDesc(keyword=[("jsonString", StringArg)])

