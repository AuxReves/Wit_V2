import sys
import os
import shutil
from pathlib import Path
import utils

def usage(pname):
    print(f"Usage: \n\t{pname} init\n\t{pname} add <absolute_path_to_resource>")



def init():
    cwd_imgs = ".wit"
    os.makedirs(cwd_imgs)
    os.chdir(cwd_imgs)
    os.makedirs("images")
    os.makedirs("staging_area")
    refs = open("references.txt", mode="w")
    refs.close()



def add(filepath):  
    # path can be a directory
    # If filepath is path/to/entry
    # And parent directory contains .wit directory
    # Then result of 'add' will be:
    # "/some_path/parent_directory/.wit/staging_area/path/to/entry"

    filepath = Path(filepath).absolute()

    if utils.is_changed(filepath):

        project_root = utils.find_project_root(filepath)
        rel_path = Path(filepath).relative_to(project_root)   
        src = filepath # Assigned for clearence
        dest = project_root / ".wit/staging_area" / rel_path

        #   2 cases handled differently: 1) file    2) direcectory
        if os.path.isfile(filepath):
            shutil.copy(src, dest) # Copy src file to dest

        elif os.path.isdir(filepath):

            if dest.exists():
                shutil.rmtree(dest)

            shutil.copytree(src, dest) # Copy src directory tree to dest

        else:
            raise ValueError(f"The path {filepath} is neither a file nor directory!")
    
    else:
        print("Tree/file is not changed. 'add' command not executed.")



def commit(msg):
    #   Context related: commit will run iff exists a parent directory to cwd with .wit directory in it. Else - Error.
    #   !Context related: commit snapshots "staging_area" directory in parent's .wit directory. 
    staged_for_commit =[]

    project_root = None
    commit_id = utils.genCommitId()
    project_root = utils.find_project_root(os.getcwd())


    with open(str(project_root) + "/.wit/references.txt", mode="r") as refs:

        if os.path.getsize(refs.name) != 0: 
            # Atleast one valid image exists

            head_image_id = utils.get_head_image_id(refs)
            head_image = project_root / ".wit/images" / head_image_id
            staging_area = project_root / ".wit/staging_area" 

            # Check if head_image and staging_area are different
            if not utils.are_dir_trees_equal(head_image, staging_area): 
                utils.create_image(project_root, commit_id, msg, head_image_id)


        else: 
            # No valid image
            utils.create_image(project_root, commit_id, msg)



def status():
    project_root = utils.find_project_root(os.getcwd())
    with open(str(project_root / ".wit/references.txt"), mode="r+") as refs:
        last_commit_id = None
        if os.path.getsize(refs.name) != 0:
            last_commit_id = utils.get_head_image_id(refs)
            print(f"Last commit's id = {last_commit_id}\n")
        else:
            print("No commit happend yet\n\n")


        
        # Now we use utils.get_head_image_id. If not None:
        # We compare the commit with staging_area - each different file will be stored and printed.
        last_commit = project_root / f".wit/images/{last_commit_id}"
        staging_area = project_root / ".wit/staging_area"
        added_list = []
        utils.files_added_since_last_commit(last_commit, project_root, staging_area, staging_area, added_list)
        added_list = [item for item in added_list if item is not None]
        print("Changes to be commited:\n")
        utils.print_list_columns(added_list)

        edited_list = []
        utils.changes_not_staged_for_commit(project_root, staging_area, staging_area, edited_list)
        edited_list = [item for item in edited_list if item is not None]
        print("Changes not staged for commit:\n")
        utils.print_list_columns(edited_list)

        unstaged_list = []
        utils.unstaged_files(project_root, staging_area, project_root, unstaged_list)
        unstaged_list = [item for item in unstaged_list if item is not None]
        print("Untracked files:\n")
        utils.print_list_columns(unstaged_list)



def main():
    argv = sys.argv
    if len(argv) < 2:
        usage(argv[0])
    else:
        if argv[1] == "init":
            # check if already initialzed
            init()
        
        if argv[1] == "add":
            add(argv[2])

        if argv[1] == "commit":
            commit(argv[2])

        if argv[1] == "status":
            status()

if __name__ == "__main__":
    main()