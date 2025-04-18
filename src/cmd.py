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
# Helper functions
# ==========================================================================

def _get_model_by_filename(session, filename):
    """Get a model by its filename."""
    mols = session.models.list(type=Structure)
    for mol in mols:
        if hasattr(mol, 'filename') and mol.filename == filename:
            return mol
    return None

def _open_model(session, filepath):
    """Open a model file and return the model."""
    try:
        model = run(session, f"open {filepath}")[0]
        # Color by chain after opening
        run(session, f"color #!{model.id_string} bychain")
        run(session, f"color #!{model.id_string} byhetero")
        return model
    except Exception as e:
        session.logger.error(f"Error opening file {filepath}: {str(e)}")
        return None

def _process_bonds(session, model, bonds):
    """Process and display bonds for a model."""
    if not bonds:
        return
        
    for bond in bonds:
        atom1 = bond.get('atom1')
        atom2 = bond.get('atom2')
        res1 = bond.get('res1')
        res2 = bond.get('res2')
        interaction = bond.get('interaction', '')
        
        if all([atom1, atom2, res1, res2]):
            # Parse residue strings to get chain and index
            chain1, index1 = res1.split(':')[:2]
            chain2, index2 = res2.split(':')[:2]
            
            # Format atom specifications for ChimeraX
            residue1 = f"#{model.id_string}/{chain1}:{index1}"  
            residue2 = f"#{model.id_string}/{chain2}:{index2}"  
            
            # Show atoms
            run(session, f"show {residue1} atoms")
            run(session, f"show {residue2} atoms")
            run(session, f"style {residue1} ball")
            run(session, f"style {residue2} ball")
            
            # Construct the pbond command with appropriate color based on interaction type
            color = "gold"  # default color
            if "HBOND" in interaction:
                color = "blue"
            elif "VDW" in interaction:
                color = "gray"
                
            # Check if atom1 and atom2 are coordinates (contain commas)
            atom1_type = "CA" if ',' in str(atom1) else atom1
            atom2_type = "CA" if ',' in str(atom2) else atom2
            
            pbond_command = f"pbond {residue1}@{atom1_type} {residue2}@{atom2_type} color {color} radius 0.1 dashes 4"
            run(session, pbond_command)
            
            # Color the atoms
            run(session, f"color {residue1} red target c")
            run(session, f"color {residue2} red target c")

# ==========================================================================
# Main command functions
# ==========================================================================

def status(session):
    """Display the current status of ProteinCraft."""
    mols = session.models.list(type=Structure)
    mol_dict = {}
    for mol in mols:
        if hasattr(mol, 'filename') and mol.filename:
            mol_dict[mol.filename] = {
                'id': mol.id_string,
                'name': mol.name,
                'display': mol.display
            }
    json_output = json.dumps(mol_dict, indent=2)
    session.logger.info(json_output)

status_desc = CmdDesc()

def sync(session, jsonString=None):
    """Synchronize with ProteinCraft using a JSON string."""
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
                mol = _get_model_by_filename(session, filepath)
                
                if mol is None:
                    # If file is not open, open it
                    mol = _open_model(session, filepath)
                
                if mol:
                    mol.display = True
                    # Process bonds if they exist
                    if 'bonds' in state:
                        _process_bonds(session, mol, state['bonds'])
        
        session.logger.info("Successfully updated model display states and bonds")
        
        # Orient the view after updating models
        run(session, "view orient")
        
    except json.JSONDecodeError:
        session.logger.error("Invalid JSON string provided")
    except Exception as e:
        session.logger.error(f"Error updating model display states: {str(e)}")

sync_desc = CmdDesc(keyword=[("jsonString", StringArg)])

