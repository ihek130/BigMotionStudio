"""
Utility Functions
Helper functions for the YouTube Automation Bot
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any


def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """Setup logging configuration"""
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"bot_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('YouTubeBot')
    logger.info(f"Logging initialized: {log_file}")
    
    return logger


def load_config(config_path: str = "config.yaml") -> Dict:
    """Load configuration from YAML file"""
    import yaml
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def load_env():
    """Load environment variables from .env file"""
    from dotenv import load_dotenv
    load_dotenv()


def ensure_directories(config: Dict):
    """Ensure all required directories exist"""
    dirs = [
        config.get('general', {}).get('output_dir', 'output'),
        config.get('general', {}).get('temp_dir', 'temp'),
        config.get('general', {}).get('logs_dir', 'logs')
    ]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)


def save_json(data: Dict, filepath: str):
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(filepath: str) -> Dict:
    """Load data from JSON file"""
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_project_metadata(project_id: str) -> Dict:
    """Get or create project metadata"""
    metadata_path = f"output/{project_id}/metadata.json"
    
    if os.path.exists(metadata_path):
        return load_json(metadata_path)
    
    metadata = {
        'project_id': project_id,
        'created_at': datetime.now().isoformat(),
        'status': 'initialized',
        'stages_completed': []
    }
    
    save_json(metadata, metadata_path)
    return metadata


def update_project_metadata(project_id: str, updates: Dict):
    """Update project metadata"""
    metadata_path = f"output/{project_id}/metadata.json"
    metadata = get_project_metadata(project_id)
    metadata.update(updates)
    metadata['updated_at'] = datetime.now().isoformat()
    save_json(metadata, metadata_path)


def clean_temp_files(temp_dir: str):
    """Clean up temporary files with retry logic for Windows file locks"""
    import shutil
    import time
    import gc
    
    if os.path.exists(temp_dir):
        # Force garbage collection to release any lingering file handles
        gc.collect()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                shutil.rmtree(temp_dir)
                os.makedirs(temp_dir, exist_ok=True)
                break
            except PermissionError as e:
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                    gc.collect()
                else:
                    # Log warning but don't fail the entire process
                    import logging
                    logging.warning(f"Could not fully clean temp dir: {e}")
