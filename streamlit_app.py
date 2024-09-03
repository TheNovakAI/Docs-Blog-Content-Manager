import streamlit as st
from github import Github
from streamlit_ace import st_ace

# Load secrets
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
REPO_NAME = "Cubs-Capital/cubsAI-SAAS"
BRANCH_NAME = "master"
DOCS_PATH = "cubsAI/blog/src/content/docs"  # Path to your docs directory

# Initialize GitHub client
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def authenticate():
    """Simple password-based authentication."""
    password = st.sidebar.text_input("Enter Admin Password", type="password")
    if password == ADMIN_PASSWORD:
        return True
    else:
        st.sidebar.error("Invalid password")
        return False

def list_files_in_folder(path):
    """List files and directories in the GitHub repo at a given path."""
    contents = repo.get_contents(path, ref=BRANCH_NAME)
    files = []
    for content in contents:
        if content.type == "dir":
            files.append({
                "type": "dir",
                "path": content.path,
                "name": content.name,
                "children": list_files_in_folder(content.path)
            })
        else:
            files.append({
                "type": "file",
                "path": content.path,
                "name": content.name
            })
    return files

def get_all_folders(files, parent_key=""):
    """Get all folder paths for dropdown."""
    folders = []
    for file in files:
        if file["type"] == "dir":
            folders.append(file["path"])
            # Recursively add subfolders
            folders.extend(get_all_folders(file["children"], parent_key=file["path"]))
    return folders

def display_sidebar_structure(files, parent_key=""):
    """Display the file structure in the sidebar with buttons for interaction."""
    for file in files:
        if file["type"] == "dir":
            # Use expander to show directories
            with st.sidebar.expander(f"📁 {file['name']}", expanded=False):
                display_sidebar_structure(file["children"], parent_key=file["path"])
        else:
            file_key = f"{parent_key}/{file['name']}"
            if st.sidebar.button(f"📝 Edit {file['name']}", key=file_key):
                st.session_state['selected_file'] = file["path"]
                st.session_state['file_content'] = load_file_content(file["path"])

def load_file_content(file_path):
    """Load the content of a file from the GitHub repo."""
    file_content = repo.get_contents(file_path, ref=BRANCH_NAME)
    return file_content.decoded_content.decode()

def update_file_content(file_path, new_content, commit_message="Update content"):
    """Update the content of a file in the GitHub repo."""
    file = repo.get_contents(file_path, ref=BRANCH_NAME)
    repo.update_file(file.path, commit_message, new_content, file.sha, branch=BRANCH_NAME)

def display_editor(file_path):
    """Display an editor to modify the content of a file."""
    st.subheader(f"Editing: {file_path}")
    
    # Only one editor box for editing content
    if 'file_content' in st.session_state:
        new_content = st_ace(
            value=st.session_state['file_content'], 
            language='markdown', 
            theme='github', 
            auto_update=False,  # Prevent updating on every keystroke
            key="editor"
        )

        if st.button("Save Changes"):
            update_file_content(file_path, new_content, f"Updated {file_path}")
            st.success(f"Updated {file_path} successfully!")
            st.session_state['file_content'] = new_content  # Update content in session state

def manage_docs():
    """Manage the docs files: add or edit existing files."""
    st.sidebar.subheader("Docs Management")
    files = list_files_in_folder(DOCS_PATH)

    # Display the file structure
    display_sidebar_structure(files)

    # Handle selected file for editing
    if 'selected_file' in st.session_state and st.session_state['selected_file']:
        display_editor(st.session_state['selected_file'])

    # Add new file option
    st.sidebar.markdown("---")
    st.sidebar.subheader("Add New Markdown File")
    
    # Get all folders for dropdown
    all_folders = get_all_folders(files)
    selected_folder = st.sidebar.selectbox("Select Folder", all_folders)

    new_file_name = st.sidebar.text_input("New File Name", "new-file.md")
    new_file_title = st.sidebar.text_input("Title", "New Title")
    new_file_description = st.sidebar.text_input("Description", "New Description")
    
    # Content for new file
    new_file_content = st.text_area("Content", "Write your markdown content here...")

    if st.sidebar.button("Create File"):
        # Add front matter (YAML) for title and description
        front_matter = f"---\ntitle: {new_file_title}\ndescription: {new_file_description}\n---\n\n"
        complete_content = front_matter + new_file_content

        new_file_path = f"{selected_folder}/{new_file_name}"
        try:
            repo.create_file(new_file_path, "Add new markdown file", complete_content)
            st.success(f"New file {new_file_name} created successfully in {selected_folder}.")
            st.session_state['selected_file'] = new_file_path  # Automatically select the new file for editing
            st.session_state['file_content'] = complete_content
        except Exception as e:
            st.error(f"Error creating file: {e}")

def main():
    st.title("THE Novak AI - Custom CMS")
    st.sidebar.title("CMS Navigation")

    # Authentication
    if not authenticate():
        st.stop()

    # Initialize session state
    if 'selected_file' not in st.session_state:
        st.session_state['selected_file'] = None
    if 'file_content' not in st.session_state:
        st.session_state['file_content'] = None

    # Manage docs files
    manage_docs()

if __name__ == "__main__":
    main()
