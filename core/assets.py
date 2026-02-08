"""
Asset handling and utilities
"""
import os
from django.conf import settings


def get_logo_paths():
    """
    Get logo paths for templates.
    Looks for dpt_logo and justujuu-logo in assets/ directory.
    Supports multiple formats: .png, .jpg, .svg, .gif
    """
    logo_formats = ['.png', '.jpg', '.jpeg', '.svg', '.gif']
    assets_dir = os.path.join(settings.BASE_DIR, 'assets')
    
    logos = {
        'dpt_logo': None,
        'justujuu_logo': None,
    }
    
    if os.path.exists(assets_dir):
        files = os.listdir(assets_dir)
        
        # Look for dpt_logo
        for f in files:
            if 'dpt_logo' in f.lower():
                logos['dpt_logo'] = f'assets/{f}'
                break
        
        # Look for justujuu-logo or justujuu_logo
        for f in files:
            if 'justujuu' in f.lower():
                logos['justujuu_logo'] = f'assets/{f}'
                break
    
    return logos
