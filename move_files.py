import os
import shutil

source_dir = 'temp_extracted/Efkv15-main'
target_dir = '.'

# Create a list of files and folders to move
files_to_move = []
dirs_to_move = []

for item in os.listdir(source_dir):
    source_path = os.path.join(source_dir, item)
    if os.path.isfile(source_path):
        files_to_move.append(item)
    elif os.path.isdir(source_path):
        dirs_to_move.append(item)

# Move files
print("Moving files...")
for file in files_to_move:
    source_path = os.path.join(source_dir, file)
    target_path = os.path.join(target_dir, file)
    
    # Check if target file exists and remove it to allow overwrite
    if os.path.exists(target_path):
        try:
            os.remove(target_path)
            print(f"Removed existing file: {target_path}")
        except Exception as e:
            print(f"Error removing file {target_path}: {e}")
    
    try:
        shutil.copy2(source_path, target_path)
        print(f"Copied: {file}")
    except Exception as e:
        print(f"Error copying file {file}: {e}")

# Move directories
print("\nMoving directories...")
for dir_name in dirs_to_move:
    source_path = os.path.join(source_dir, dir_name)
    target_path = os.path.join(target_dir, dir_name)
    
    # Remove target directory if it exists
    if os.path.exists(target_path):
        try:
            shutil.rmtree(target_path)
            print(f"Removed existing directory: {target_path}")
        except Exception as e:
            print(f"Error removing directory {target_path}: {e}")
    
    try:
        shutil.copytree(source_path, target_path)
        print(f"Copied directory: {dir_name}")
    except Exception as e:
        print(f"Error copying directory {dir_name}: {e}")

print("\nFile moving completed!")