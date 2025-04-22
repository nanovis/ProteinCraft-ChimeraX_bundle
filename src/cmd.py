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
from .ProteinCraftData import ProteinCraftData, BondDetailType  # Import the new class and enum
from pathlib import Path                        # For file path operations

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
        # Get file extension using pathlib
        ext = Path(filepath).suffix.lower()
        format_str = "pdb" if ext.startswith(".pdb") else "cif" 
        
        model = run(session, f"open {filepath} format {format_str}")[0]
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
    """Process and display bonds for a model.
    
    Returns:
        bool: True if all bonds were processed successfully, False otherwise
    """
    if not bonds:
        return True
        
    # Get current bond detail type
    bond_detail = ProteinCraftData.get_instance().get_bond_detail()

    print("Length of bonds: ", len(bonds))
    
    # For AUTO mode, determine if we should show CA or ATOM based on bond count
    if bond_detail == BondDetailType.AUTO:
        print("Bond detail is AUTO")
        if len(bonds) > 3:
            bond_detail = BondDetailType.CA
        else:
            bond_detail = BondDetailType.ATOM

    print("Bond detail is now: ", bond_detail)
    
    success = True
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

            # Color the residues cartoon
            run(session, f"color {residue1} red target c")
            run(session, f"color {residue2} red target c")
            
            # Construct the pbond command with appropriate color based on interaction type
            color = "gold"  # default color
            interaction_upper = interaction.upper()
            if "HBOND" in interaction_upper:
                color = "#1f77b4"         # H‑Bond (light blue)
            elif "PIPISTACK" in interaction_upper:
                color = "#ff7f0e"         # π‑π Stack (orange)
            elif "PICATION" in interaction_upper:
                color = "#2ca02c"         # π‑Cation (green)
            elif "IONIC" in interaction_upper:
                color = "#d62728"         # Ionic (red)
            elif "DISULPHIDE" in interaction_upper:
                color = "#9467bd"         # Disulphide (purple)
            elif "METAL" in interaction_upper:
                color = "#e377c2"         # Metal Coordination (pink)
            elif "PIH" in interaction_upper:  # covers π‑H Bond
                color = "#bcbd22"         # π‑H Bond (yellow‑green)
            elif "HALOGEN" in interaction_upper:
                color = "#17becf"         # Halogen (cyan)
            elif "VDW" in interaction_upper:
                color = "#7f7f7f"         # van der Waals (gray)
            elif "IAC" in interaction_upper:
                color = "#8c564b"         # IAC (brown)
            else:
                color = "gold"            # fallback
            
            # Handle atom specifications based on bond detail type
            if bond_detail == BondDetailType.CA:
                # For CA mode, always use CA atoms
                atom1_spec = f"{residue1}@CA"
                atom2_spec = f"{residue2}@CA"
                print("Atom1 spec: ", atom1_spec)
                print("Atom2 spec: ", atom2_spec)
            else:
                # For ATOM mode, use the specified atoms
                if ',' in str(atom1):
                    marker1 = f"marker #{model.id_string}.43 position {atom1} color gray radius 0.12"
                    marker1_obj = run(session, marker1)
                    marker1_obj.structure.name = "ProteinCraftMarkers"
                    atom1_spec = f"#{model.id_string}.43:{marker1_obj.serial_number}"
                else:
                    atom1_spec = f"{residue1}@{atom1}"
                
                if ',' in str(atom2):
                    marker2 = f"marker #{model.id_string}.43 position {atom2} color gray radius 0.12"
                    marker2_obj = run(session, marker2)
                    marker2_obj.structure.name = "ProteinCraftMarkers"
                    atom2_spec = f"#{model.id_string}.43:{marker2_obj.serial_number}"
                else:
                    atom2_spec = f"{residue2}@{atom2}"

                # Show atoms
                run(session, f"show {residue1} atoms")
                run(session, f"show {residue2} atoms")
                run(session, f"style {residue1} ball")
                run(session, f"style {residue2} ball")
                run(session, f"cartoon {residue1} suppressBackboneDisplay false")
                run(session, f"cartoon {residue2} suppressBackboneDisplay false")

            # Use the appropriate specifications in pbond command
            pbond_command = f"pbond {atom1_spec} {atom2_spec} color {color} radius 0.1 dashes 4 name ProteinCraftBonds"
            run(session, pbond_command)
            
    return success

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
        # Store the JSON string
        ProteinCraftData.get_instance().set_json_string(jsonString)
        
        # Parse the JSON string
        display_states = json.loads(jsonString)
        
        # Get all open structure models
        mols = session.models.list(type=Structure)
        
        # First, set display to False for all currently open models
        for mol in mols:
            if hasattr(mol, 'filename') and mol.filename:
                mol.display = False

            # Delete existing ProteinCraftBonds submodels
            for submodel in mol.child_models():
                if submodel.name == "ProteinCraftBonds" or submodel.name == "ProteinCraftMarkers":
                    session.models.close([submodel])
        
        success = True
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
                        success = _process_bonds(session, mol, state['bonds'])
        
        run(session, "cartoon tether opacity 0")
        
        if success:
            session.logger.info("Successfully updated model display states and bonds")
        else:
            session.logger.warning("Failed to process some bonds")
        
    except json.JSONDecodeError:
        session.logger.error("Invalid JSON string provided")
    except Exception as e:
        session.logger.error(f"Error updating model display states: {str(e)}")

sync_desc = CmdDesc(keyword=[("jsonString", StringArg)])

def printJson(session):
    """Print the stored JSON string from ProteinCraftData."""
    json_string = ProteinCraftData.get_instance().get_json_string()
    if json_string is None:
        session.logger.warning("No JSON string has been stored yet")
    else:
        session.logger.info(json_string)

printJson_desc = CmdDesc()

def bondDetail(session, detail_type=None):
    """Show or set the bond detail type (CA/ATOM/AUTO)."""
    if detail_type is None:
        # Show current bond detail type
        current_type = ProteinCraftData.get_instance().get_bond_detail()
        session.logger.info(f"Current bond detail type: {current_type.value}")
    else:
        # Set new bond detail type
        try:
            new_type = BondDetailType(detail_type.upper())
            ProteinCraftData.get_instance().set_bond_detail(new_type)
            session.logger.info(f"Bond detail type set to: {new_type.value}")
        except ValueError:
            session.logger.error(f"Invalid bond detail type. Must be one of: {', '.join(t.value for t in BondDetailType)}")

bondDetail_desc = CmdDesc(
    optional=[("detail_type", StringArg)],
    synopsis="Show or set bond detail type"
)

