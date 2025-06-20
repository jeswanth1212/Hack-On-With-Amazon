import os
import sys

# Create a data -> database symbolic link
src_dir = os.path.join(os.getcwd(), 'src')

# Create a data directory if it doesn't exist
data_dir = os.path.join(src_dir, 'data')
os.makedirs(data_dir, exist_ok=True)

# Create an __init__.py file in the data directory
with open(os.path.join(data_dir, '__init__.py'), 'w') as f:
    f.write('# This is a compatibility layer for src.data -> src.database\n')
    f.write('from src.database import *\n')

# Create a symlink for database.py in the data directory
with open(os.path.join(data_dir, 'database.py'), 'w') as f:
    f.write('# This file redirects imports to the actual database module\n')
    f.write('from src.database.database import *\n')

# Create symlinks for other files if needed
with open(os.path.join(data_dir, 'preprocess.py'), 'w') as f:
    f.write('# This file redirects imports to the actual preprocess module\n')
    f.write('from src.database.preprocess import *\n')

with open(os.path.join(data_dir, 'download.py'), 'w') as f:
    f.write('# This file redirects imports to the actual download module\n')
    f.write('from src.database.download import *\n')

print("Import fixes applied successfully!") 