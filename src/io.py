# vim: set expandtab shiftwidth=4 softtabstop=4:

import json
from chimerax.core.commands import run
from .cmd import _open_model, _process_bonds
from chimerax.atomic import Structure, AtomicStructure
from .ProteinCraftData import ProteinCraftData
from numpy import array, float64
from chimerax.atomic.struct_edit import add_atom

def _read_pdb_block(session, stream, line_number=0):
    """Read a single block from a PDB file.
    
    Args:
        session: The ChimeraX session
        stream: File data stream
        line_number: Current line number in the file
        
    Returns:
        tuple: (AtomicStructure instance, line_number) or (None, line_number) if EOF
    """
    # Create the AtomicStructure instance
    s = AtomicStructure(session)
    current_chain = None
    current_residue = None
    current_residue_number = None
    
    while True:
        line = stream.readline()
        if not line:
            break
        line_number += 1
        
        # Skip non-ATOM/HETATM lines
        if not (line.startswith('ATOM') or line.startswith('HETATM')):
            continue
            
        # Parse atom data
        try:
            atom_name = line[12:16].strip()
            res_name = line[17:20].strip()
            chain_id = line[21]
            res_number = int(line[22:26])
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
            element = line[76:78].strip()
            
            # Create new chain if needed
            if chain_id != current_chain:
                current_chain = chain_id
                
            # Create new residue if needed
            if res_number != current_residue_number:
                current_residue = s.new_residue(res_name, chain_id, res_number)
                current_residue_number = res_number
                
            # Create atom
            atom = add_atom(atom_name, 
                            element, 
                            current_residue, 
                            array([x, y, z], dtype=float64))
            
        except (ValueError, IndexError) as e:
            session.logger.error(f"Error parsing PDB line {line_number}: {str(e)}")
            continue
            
    # Use AtomicStructure method to add bonds based on interatomic distances
    s.connect_structure()
    
    return s, line_number

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
        pdb_path = pcraftin_data['input_pdb']
                
        with open(pdb_path, 'r') as pdb_file:
            model, _ = _read_pdb_block(session, pdb_file)
        if model is None:
            session.logger.error(f"Failed to open PDB file: {pdb_path}")
            return [], f"Failed to open PDB file: {pdb_path}"
            
        # Apply default colors from ProteinCraftData
        chain_a_color = ProteinCraftData.CHAIN_A_COLOR
        chain_b_color = ProteinCraftData.CHAIN_B_COLOR
        
        status = f"Opened ProteinCraft input file {file_name}"
        return [model], status
        
    except Exception as e:
        session.logger.error(f"Error opening ProteinCraft input file: {str(e)}")
        return [], f"Error opening ProteinCraft input file: {str(e)}"