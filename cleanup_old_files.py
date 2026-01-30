"""
Cleanup Old Temp Files
=======================
Automatically deletes temp files older than 2 hours.
Run as cron job every hour to keep storage minimal.

Usage:
    python cleanup_old_files.py

Or via cron/Task Scheduler:
    0 * * * * python cleanup_old_files.py  # Run every hour
"""

import os
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def cleanup_old_temp_files(temp_dir: str = "temp", max_age_hours: int = 2):
    """
    Delete temp files older than max_age_hours.
    
    Args:
        temp_dir: Path to temp directory
        max_age_hours: Delete files older than this many hours
    """
    if not os.path.exists(temp_dir):
        logger.info(f"Temp directory does not exist: {temp_dir}")
        return
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    deleted_count = 0
    kept_count = 0
    total_freed_mb = 0
    
    logger.info(f"🧹 Starting cleanup of files older than {max_age_hours} hours...")
    logger.info(f"   Cutoff time: {cutoff_time}")
    
    # Iterate through project folders in temp/
    for project_id in os.listdir(temp_dir):
        project_path = os.path.join(temp_dir, project_id)
        
        # Skip if not a directory
        if not os.path.isdir(project_path):
            continue
        
        try:
            # Get folder creation time
            folder_created = datetime.fromtimestamp(os.path.getctime(project_path))
            
            # Check if folder is old enough to delete
            if folder_created < cutoff_time:
                # Calculate folder size
                folder_size_mb = get_folder_size(project_path) / (1024 * 1024)
                
                # Delete folder
                shutil.rmtree(project_path)
                deleted_count += 1
                total_freed_mb += folder_size_mb
                
                logger.info(f"   ✅ Deleted: {project_id} (age: {datetime.now() - folder_created}, size: {folder_size_mb:.1f} MB)")
            else:
                kept_count += 1
                age_minutes = (datetime.now() - folder_created).total_seconds() / 60
                logger.debug(f"   ⏳ Kept: {project_id} (age: {age_minutes:.0f} minutes)")
                
        except Exception as e:
            logger.error(f"   ❌ Error processing {project_id}: {e}")
    
    logger.info(f"")
    logger.info(f"📊 Cleanup Summary:")
    logger.info(f"   Deleted: {deleted_count} folders")
    logger.info(f"   Kept: {kept_count} folders")
    logger.info(f"   Space freed: {total_freed_mb:.1f} MB")
    logger.info(f"")


def get_folder_size(folder_path: str) -> int:
    """Calculate total size of folder in bytes"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        logger.error(f"Error calculating folder size: {e}")
    
    return total_size


def cleanup_output_folder(output_dir: str = "output", max_age_days: int = 7):
    """
    Clean up old projects from output folder (for videos that failed to upload).
    More conservative - keeps files for 7 days.
    """
    if not os.path.exists(output_dir):
        logger.info(f"Output directory does not exist: {output_dir}")
        return
    
    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    deleted_count = 0
    total_freed_mb = 0
    
    logger.info(f"🧹 Starting cleanup of output files older than {max_age_days} days...")
    
    for project_id in os.listdir(output_dir):
        project_path = os.path.join(output_dir, project_id)
        
        if not os.path.isdir(project_path):
            continue
        
        try:
            folder_created = datetime.fromtimestamp(os.path.getctime(project_path))
            
            if folder_created < cutoff_time:
                folder_size_mb = get_folder_size(project_path) / (1024 * 1024)
                shutil.rmtree(project_path)
                deleted_count += 1
                total_freed_mb += folder_size_mb
                
                logger.info(f"   ✅ Deleted: {project_id} (age: {datetime.now() - folder_created}, size: {folder_size_mb:.1f} MB)")
                
        except Exception as e:
            logger.error(f"   ❌ Error processing {project_id}: {e}")
    
    logger.info(f"📊 Output cleanup: Deleted {deleted_count} folders, freed {total_freed_mb:.1f} MB")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🧹 AUTOMATED CLEANUP STARTED")
    logger.info("=" * 60)
    
    # Cleanup temp files older than 2 hours
    cleanup_old_temp_files(temp_dir="temp", max_age_hours=2)
    
    # Cleanup output files older than 7 days (failed uploads)
    cleanup_output_folder(output_dir="output", max_age_days=7)
    
    logger.info("=" * 60)
    logger.info("✅ CLEANUP COMPLETE")
    logger.info("=" * 60)
