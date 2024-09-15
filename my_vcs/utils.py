import os
import shutil
import filecmp
import string
import random
from datetime import datetime
from pathlib import Path



def create_image(project_root, commit_id, msg, head=None):
    src, dest = project_root / ".wit/staging_area", project_root / ".wit/images" /  commit_id
    shutil.copytree(src, dest, dirs_exist_ok=True)

    with open(str(project_root) + "/.wit/images/" + commit_id + ".txt", mode="w") as image_md:
        image_md.write(f"parent={head}\ndate={datetime.now()}\nMessage={msg}\n")

    with open(str(project_root) + "/.wit/references.txt", mode = "w") as refs:
        refs.write(f"HEAD={commit_id}\nmaster={commit_id}\n")


def are_dir_trees_equal(dir1, dir2):
    cmp = filecmp.dircmp(dir1, dir2)
    if len(cmp.left_only) > 0 or len(cmp.right_only) > 0 or len(cmp.funny_files) > 0:
        return False

    (_, mismatch, errors) = filecmp.cmpfiles(dir1, dir2, cmp.common_files, shallow=False)
    if len(mismatch) > 0 or len(errors) > 0:
        return False
    
    for common_dir in cmp.common_dirs:
        dir1 = os.path.join(dir1, common_dir)
        dir2 = os.path.join(dir2, common_dir)
        if not are_dir_trees_equal(dir1, dir2):
            return False
    
    return True
    


def find_project_root(path):

    project_root = Path(path)
    # path may be file and not directory - check first

    ## Changed from os.path.isdir(path) and (path / ".wit").exists() to ->
    if project_root.is_dir() and (project_root / ".wit").exists(): #
        return project_root
    

    # Either path is a file, or path is not root. Search up the filesystem tree.
    project_root = project_root.parent

    while not (project_root / ".wit").exists():  #   Find "root" of our version controlled project (closest parent with .wit directory)
        if project_root == project_root.parent:
            raise FileNotFoundError("No parent directory containing .wit directory - no root for project initialized by .wit!")
        project_root = Path(project_root).parent

    return project_root 



def is_changed(path): 

    # assume path is absolute
    # check if a file with same name resides in staging_area
    project_root = find_project_root(path)
    staging_area = project_root / ".wit/staging_area"
    rel_path_to_project_root = Path(str(Path(path).relative_to(project_root)))
    absolute_path_to_backup = str(staging_area / rel_path_to_project_root)

    if not os.path.exists(absolute_path_to_backup):
        return True
    
    absolute_path_to_entry = project_root / rel_path_to_project_root

    if os.path.isfile(str(absolute_path_to_entry)) and os.path.isfile(str(absolute_path_to_backup)):
        return not filecmp.cmp(absolute_path_to_entry, absolute_path_to_backup, shallow=False)
    
    elif os.path.isdir(str(absolute_path_to_entry)) and os.path.isdir(str(absolute_path_to_backup)):
        return are_dir_trees_equal(absolute_path_to_entry, absolute_path_to_backup)

'''
THE FOLLOWING 3 METHODS WILL BE REFACTORED INTO 1 GENERIC FUNCTION
'''
# A recursive function that checks for difference.
def files_added_since_last_commit(last_commit, project_root, staging_area, entry_to_check, added_list):
    # entry_to_check is absolute path
    entry_to_check = Path(entry_to_check)

    if entry_to_check.is_dir():
        curr_dir = entry_to_check
        # curr_dir is in staging_area - check if it's in the last commit
        # if not - then it was added.
        # if it is - check if content is different.
        # if it is - then it was added.
        # else - not added.

        for entry in curr_dir.iterdir():
            added_list.append(files_added_since_last_commit(last_commit, project_root, staging_area, entry, added_list))
    elif entry_to_check.is_file():
        rel_path_to_entry_from_staging_area_str = str(entry_to_check.relative_to(staging_area))
        abs_path_to_entris_copy_in_last_commit = last_commit / rel_path_to_entry_from_staging_area_str
        if abs_path_to_entris_copy_in_last_commit.exists():
            if not filecmp.cmp(str(entry_to_check.absolute()), abs_path_to_entris_copy_in_last_commit, shallow=False):
                return entry_to_check
            
        else:
            return str(project_root / rel_path_to_entry_from_staging_area_str)
    
    else:
        raise FileNotFoundError("For now file not found - should be custom error!")
    


def changes_not_staged_for_commit(project_root, staging_area, entry_to_check, edited_list):
    entry_to_check = Path(entry_to_check)

    if entry_to_check.is_dir():
        curr_dir = entry_to_check

        for entry in curr_dir.iterdir():
            edited_list.append(changes_not_staged_for_commit(project_root, staging_area, entry, edited_list))

    elif entry_to_check.is_file():
        rel_path_to_entry_from_staging_area = entry_to_check.relative_to(staging_area)
        abs_path_to_entry_in_project_root = project_root / str(rel_path_to_entry_from_staging_area)

        if abs_path_to_entry_in_project_root.exists():
            if not filecmp.cmp(entry_to_check.absolute(), abs_path_to_entry_in_project_root, shallow=False):
                return entry_to_check
        
    else:
        raise FileNotFoundError("For now file not found - should be custom error!")

    

def unstaged_files(project_root, staging_area, entry_to_check, unstaged_list):
    entry_to_check = Path(entry_to_check)
    if entry_to_check.is_dir():

        path_to_entry_as_list = str(entry_to_check).split("/")
        if path_to_entry_as_list[len(path_to_entry_as_list) - 1] == ".wit":
            return None
        curr_dir = entry_to_check

        for entry in curr_dir.iterdir():
            unstaged_list.append(unstaged_files(project_root, staging_area, entry, unstaged_list))

    elif entry_to_check.is_file():
        rel_path_to_entry_from_project_root = entry_to_check.relative_to(project_root)
        abs_path_to_entry_in_staging_area = staging_area / rel_path_to_entry_from_project_root
        if not abs_path_to_entry_in_staging_area.exists():
            return entry_to_check
        
'''
THE ABOVE 3 METHODS WILL BE REFACTORED INTO 1 GENERIC FUNCTION
''' 


def get_head_image_id(refs):
    head_image = ""

    while True:
            c = refs.read(1)

            if c == '\n':
                break
            
            head_image += c
        
    return head_image.split('=')[1]



def print_list_columns(list_to_print):
    for i in range(0, len(list_to_print), 2):
        print("\t".join(map(str, list_to_print[i: i + 2])))



def genCommitId():
    chars = string.digits + "abcdef"
    commit_id = ''.join(random.choices(chars, k = 40))
    return  commit_id