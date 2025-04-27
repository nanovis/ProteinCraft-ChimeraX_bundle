# vim: set expandtab shiftwidth=4 softtabstop=4:

import json
from chimerax.core.commands import run
from .cmd import _open_model, _process_bonds

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
        
        # Open the PDB file
        pdb_path = pcraftin_data['input_pdb']
        model = _open_model(session, pdb_path)
        
        if model is None:
            session.logger.error(f"Failed to open PDB file: {pdb_path}")
            return [], f"Failed to open PDB file: {pdb_path}"
            
        # Process and display bonds if they exist
        if 'pbonds' in pcraftin_data:
            _process_bonds(session, model, model.chain_a_color, pcraftin_data['pbonds'])
            
        status = f"Opened ProteinCraft input file {file_name}"
        return [model], status
        
    except Exception as e:
        session.logger.error(f"Error opening ProteinCraft input file: {str(e)}")
        return [], f"Error opening ProteinCraft input file: {str(e)}" 