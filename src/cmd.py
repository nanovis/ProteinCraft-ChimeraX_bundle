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

def _get_correct_atom_name(session, model, residue_spec, atom_name):
    """Find the correct atom name that ChimeraX recognizes.
    
    Args:
        session: ChimeraX session
        model: Structure model
        residue_spec: Residue specification (e.g. "A:1")
        atom_name: Original atom name to check
    
    Returns:
        str: Correct atom name that exists in ChimeraX, or None if not found
    """
    # First try the exact name
    try:
        result = run(session, f"select {residue_spec}@{atom_name}")
        if result and result.num_atoms > 0:
            run(session, f"~select {residue_spec}@{atom_name}")
            return atom_name
    except:
        pass
    
    # Handle cases where last digit moves to beginning (e.g. "HD12" -> "2HD1")
    if len(atom_name) >= 3 and atom_name[-1].isdigit():
        # Extract the last digit
        last_digit = atom_name[-1]
        # Remove the last digit from the original name
        base_name = atom_name[:-1]
        # Create the new name with the digit at the beginning
        new_name = f"{last_digit}{base_name}"
        
        try:
            result = run(session, f"select {residue_spec}@{new_name}")
            if result and result.num_atoms > 0:
                run(session, f"~select {residue_spec}@{new_name}")
                return new_name
        except:
            pass
    
    return None

def _process_bonds(session, model, bonds):
    """Process and display bonds for a model."""
    if not bonds:
        return
        
    # Delete existing ProteinCraftBonds submodels
    for submodel in model.child_models():
        if submodel.name == "ProteinCraftBonds" or submodel.name == "ProteinCraftMarkers":
            session.models.close([submodel])
        
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
            
            # Get correct atom names
            atom1 = _get_correct_atom_name(session, model, residue1, atom1)
            atom2 = _get_correct_atom_name(session, model, residue2, atom2)
            
            if not atom1 or not atom2:
                session.logger.warning(f"Could not find matching atoms for bond between {res1}@{bond.get('atom1')} and {res2}@{bond.get('atom2')}")
                continue
            
            # Show atoms
            run(session, f"show {residue1} atoms")
            run(session, f"show {residue2} atoms")
            run(session, f"style {residue1} ball")
            run(session, f"style {residue2} ball")
            run(session, f"cartoon {residue1} suppressBackboneDisplay false")
            run(session, f"cartoon {residue2} suppressBackboneDisplay false")
            
            # Construct the pbond command with appropriate color based on interaction type
            color = "gold"  # default color
            if "HBOND" in interaction:
                color = "blue"
            elif "VDW" in interaction:
                color = "gray"
            
            # Handle coordinate-based atoms
            if ',' in str(atom1) and ',' in str(atom2):
                # Create markers for coordinate-based atoms
                marker1 = f"marker #{model.id_string}.43 position {atom1} color gray radius 0.12"
                marker2 = f"marker #{model.id_string}.43 position {atom2} color gray radius 0.12"
                marker1_obj = run(session, marker1)
                marker2_obj = run(session, marker2)
                marker1_obj.structure.name = "ProteinCraftMarkers"
                marker2_obj.structure.name = "ProteinCraftMarkers"

                # Use the markers in pbond command
                pbond_command = f"pbond #{model.id_string}.43:{marker1_obj.serial_number} #{model.id_string}.43:{marker2_obj.serial_number} color {color} radius 0.1 dashes 4 name ProteinCraftBonds"
            else:
                # Use regular atom specifications
                pbond_command = f"pbond {residue1}@{atom1} {residue2}@{atom2} color {color} radius 0.1 dashes 4 name ProteinCraftBonds"
            
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
                    run(session, f"color #!{mol.id_string} bychain")
                    run(session, f"color #!{mol.id_string} byhetero")
                    run(session, f"hide #!{mol.id_string} atoms")
                    mol.display = True
                    # Process bonds if they exist
                    if 'bonds' in state:
                        _process_bonds(session, mol, state['bonds'])
        
        session.logger.info("Successfully updated model display states and bonds")
        
    except json.JSONDecodeError:
        session.logger.error("Invalid JSON string provided")
    except Exception as e:
        session.logger.error(f"Error updating model display states: {str(e)}")

sync_desc = CmdDesc(keyword=[("jsonString", StringArg)])

