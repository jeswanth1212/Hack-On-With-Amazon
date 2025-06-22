#!/usr/bin/env python3
"""
Kill any process currently using port 8080.
Run this before starting the server if you encounter port conflicts.
"""

import os
import sys
import subprocess
import logging
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_admin():
    """Check if running with admin/root privileges."""
    try:
        if platform.system() == 'Windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # For Unix systems
            return os.geteuid() == 0
    except:
        return False

def kill_process_on_port(port=8080):
    """Kill any process using the specified port."""
    try:
        system = platform.system()
        
        if system == 'Windows':
            # Get process ID using netstat
            logger.info(f"Looking for processes using port {port}...")
            cmd = f'netstat -ano | findstr :{port}'
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            
            if not result:
                logger.info(f"No process found using port {port}")
                return True
            
            logger.info(f"Found the following connections on port {port}:")
            print(result)
            
            # Extract PIDs - last column in netstat output
            pids = set()
            for line in result.strip().split('\n'):
                if f":{port}" in line:
                    parts = [p for p in line.strip().split(' ') if p]
                    if len(parts) >= 5:
                        pids.add(parts[-1])
            
            if not pids:
                logger.info("No process IDs found")
                return False
                
            # Kill each process
            for pid in pids:
                try:
                    logger.info(f"Attempting to kill process with PID {pid}...")
                    subprocess.check_output(f'taskkill /F /PID {pid}', shell=True)
                    logger.info(f"Successfully killed process {pid}")
                except subprocess.CalledProcessError as e:
                    if not is_admin():
                        logger.error(f"Failed to kill process {pid}. Try running as administrator: {e}")
                    else:
                        logger.error(f"Failed to kill process {pid}: {e}")
        
        elif system in ['Linux', 'Darwin']:  # Linux or macOS
            # Find PID using port
            cmd = f"lsof -i :{port} -t"
            try:
                pids = subprocess.check_output(cmd, shell=True).decode('utf-8').strip().split('\n')
                
                if not pids or (len(pids) == 1 and not pids[0]):
                    logger.info(f"No process found using port {port}")
                    return True
                    
                # Kill each process
                for pid in pids:
                    if pid:
                        logger.info(f"Attempting to kill process with PID {pid}...")
                        subprocess.check_output(f'kill -9 {pid}', shell=True)
                        logger.info(f"Successfully killed process {pid}")
                
            except subprocess.CalledProcessError:
                logger.info(f"No process found using port {port}")
                return True
        
        else:
            logger.error(f"Unsupported operating system: {system}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error killing process on port {port}: {e}")
        return False

if __name__ == "__main__":
    if is_admin():
        logger.info("Running with administrator privileges")
    else:
        logger.warning("Not running with administrator privileges. May not be able to kill all processes.")
    
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    if kill_process_on_port(port):
        logger.info(f"Finished attempting to free port {port}")
    else:
        logger.warning(f"Could not completely free port {port}") 