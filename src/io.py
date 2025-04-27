# vim: set expandtab shiftwidth=4 softtabstop=4:

import json
from chimerax.core.commands import run
from .cmd import _open_model, _process_bonds
from chimerax.atomic import Structure
from .ProteinCraftData import ProteinCraftData

def open_pcraftin(session, data, file_name, **kw):
    """Open a ProteinCraft input file.
    
    Args:
        session: The ChimeraX session
        data: File data stream
        file_name: Name of the file being opened
        **kw: Additional keyword arguments
        
    Returns:
        tuple: (list of models created, status message)
    """
    try:
        # Parse the JSON data
        pcraftin_data = json.load(data)
        
        # Check if the model is already open
        pdb_path = pcraftin_data['input_pdb']
        existing_models = session.models.list(type=Structure)
        model = None
        
        for m in existing_models:
            if hasattr(m, 'filename') and m.filename == pdb_path:
                model = m
                break
                
        # If model not found, open it
        if model is None:
            model = _open_model(session, pdb_path)
            if model is None:
                session.logger.error(f"Failed to open PDB file: {pdb_path}")
                return [], f"Failed to open PDB file: {pdb_path}"
            
        # Apply default colors from ProteinCraftData
        chain_a_color = ProteinCraftData.CHAIN_A_COLOR
        chain_b_color = ProteinCraftData.CHAIN_B_COLOR
        run(session, 
            f"color #{model.id_string}/A {chain_a_color} transparency 0; "
            f"color #{model.id_string}/B {chain_b_color}; "
            f"color #{model.id_string} byhetero; "
            f"hide #{model.id_string} atoms",
            log=False)
            
        # Process and display bonds if they exist
        if 'pbonds' in pcraftin_data:
            _process_bonds(session, model, chain_a_color, pcraftin_data['pbonds'])
            
        status = f"Opened ProteinCraft input file {file_name}"
        return [model], status
        
    except Exception as e:
        session.logger.error(f"Error opening ProteinCraft input file: {str(e)}")
        return [], f"Error opening ProteinCraft input file: {str(e)}" 