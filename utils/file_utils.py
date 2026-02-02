import os
import shutil

def list_pdf_files(directory):
    """
    Returns a list of PDF files in the given directory.
    """
    if not os.path.exists(directory):
        return []
    
    return [
        os.path.join(directory, f) 
        for f in os.listdir(directory) 
        if f.lower().endswith('.pdf')
    ]

def move_file(src_path, dest_folder):
    """
    Moves a file to the destination folder. Creates folder if needed.
    """
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
        
    try:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(dest_folder, filename)
        
        # Handle duplicate filenames in destination
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_folder, f"{base}_{counter}{ext}")
            counter += 1
            
        shutil.move(src_path, dest_path)
        return dest_path
    except Exception as e:
        print(f"Error moving file {src_path}: {e}")
        return None

def clear_data(directories, files):
    """
    Clears all data in specified directories and deletes specified files.
    """
    # Clear directories
    for directory in directories:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")

    # Delete specific files
    for file_path in files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

def reset_processed_files(processed_dir, raw_dir):
    """
    Moves all files from processed directory back to raw directory for re-processing.
    Returns the number of files moved.
    """
    if not os.path.exists(processed_dir):
        return 0
        
    count = 0
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)
        
    for filename in os.listdir(processed_dir):
        src = os.path.join(processed_dir, filename)
        if os.path.isfile(src) and filename.lower().endswith('.pdf'):
            try:
                # Use move_file logic or simple shutil
                # We can reuse move_file but we need to handle the import or just simple move logic
                # move_file handles duplicates which is good.
                move_file(src, raw_dir)
                count += 1
            except Exception as e:
                print(f"Failed to reset {filename}: {e}")
    return count
