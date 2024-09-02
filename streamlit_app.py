import streamlit as st
from github import Github
from streamlit_ace import st_ace
import re

# Load secrets
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
REPO_NAME = "Cubs-Capital/cubsAI-SAAS"
BRANCH_NAME = "master"
BLOG_PATH = "cubsAI/blog/src/content/docs"
CONFIG_PATH = "cubsAI/blog/astro.config.mjs"  # Path to the config file

# Initialize GitHub client
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def authenticate():
    """Simple password-based authentication"""
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

def load_file_content(file_path):
    """Load the content of a file from the GitHub repo."""
    file_content = repo.get_contents(file_path, ref=BRANCH_NAME)
    return file_content.decoded_content.decode()

def update_sidebar_config(js_content, new_sidebar):
    """Update the sidebar configuration in the JavaScript file."""
    new_sidebar_str = f"sidebar: {new_sidebar}"
    updated_js_content = re.sub(r"sidebar:\s*\[.*?\]", new_sidebar_str, js_content, flags=re.DOTALL)
    return updated_js_content

def update_file_content(file_path, new_content, commit_message="Update content"):
    """Update the content of a file in the GitHub repo."""
    file = repo.get_contents(file_path, ref=BRANCH_NAME)
    repo.update_file(file.path, commit_message, new_content, file.sha, branch=BRANCH_NAME)

def display_editor(file_path):
    """Display an editor to modify the content of a file."""
    st.subheader(f"Editing: {file_path}")
    current_content = load_file_content(file_path)
    new_content = st_ace(value=current_content, language='markdown', theme='github', auto_update=True)
    
    if st.button("Save Changes"):
        update_file_content(file_path, new_content, f"Updated {file_path}")
        st.success(f"Updated {file_path} successfully!")

def display_sidebar_structure(integrations, files, selected_file):
    """Display the sidebar structure based on the config file."""
    for integration in integrations:
        if 'starlight' in integration:
            sidebar = integration['starlight'].get('sidebar', [])
            for section in sidebar:
                st.sidebar.markdown(f"**{section['label']}**")
                for item in section['items']:
                    file_path = f"{BLOG_PATH}/{item['link'].strip('/')}.md"
                    # Check if file path exists in repo files
                    if any(file['path'] == file_path for file in files):
                        if st.sidebar.button(f"📝 {item['label']}", key=item['link']):
                            st.session_state['selected_file'] = file_path
                            selected_file[0] = file_path

def manage_blog_posts():
    """Manage blog posts: add new or delete existing."""
    st.sidebar.subheader("Blog Post Management")
    files = list_files_in_folder(BLOG_PATH)
    selected_file = [st.session_state.get('selected_file')]

    js_content = load_file_content(CONFIG_PATH)
    # Just locate the sidebar config for manual adjustments.
    current_sidebar = re.search(r"sidebar:\s*(\[.*?\])", js_content, re.DOTALL)
    
    if current_sidebar:
        sidebar_config = current_sidebar.group(1)
        display_sidebar_structure(eval(sidebar_config), files, selected_file)
    
    if selected_file[0]:
        display_editor(selected_file[0])
    
    if st.sidebar.button("Add New Blog Post"):
        new_blog_name = st.sidebar.text_input("New Blog Filename", "new-blog.md")
        new_blog_content = st_ace(language='markdown', theme='github')
        
        if st.sidebar.button("Create Blog Post"):
            new_blog_path = f"{BLOG_PATH}/{new_blog_name}"
            repo.create_file(new_blog_path, "Add new blog post", new_blog_content)
            st.success(f"New blog post {new_blog_name} created successfully.")
            
            # Update the sidebar dynamically (assumes Python-like list)
            new_sidebar = eval(sidebar_config)
            new_sidebar.append({"label": new_blog_name.replace("-", " ").title(), "link": f"/{new_blog_name.replace('.md', '')}"})
            updated_js_content = update_sidebar_config(js_content, new_sidebar)
            update_file_content(CONFIG_PATH, updated_js_content, "Updated astro.config.mjs with new sidebar structure")

def manage_config():
    """Manage the Astro config file to adjust sidebar and blog settings."""
    st.sidebar.subheader("Config File Management")
    js_content = load_file_content(CONFIG_PATH)
    
    # Display config content in the editor
    st.subheader("Editing Config File")
    new_js_content = st_ace(value=js_content, language='javascript', theme='github', auto_update=True)
    
    if st.button("Save Config Changes"):
        update_file_content(CONFIG_PATH, new_js_content, "Updated astro.config.mjs")
        st.success("Config file updated successfully!")

def main():
    st.title("THE Novak AI - Custom CMS")
    st.sidebar.title("CMS Navigation")

    # Authentication
    if not authenticate():
        st.stop()

    # Initialize session state
    if 'selected_file' not in st.session_state:
        st.session_state['selected_file'] = None

    # CMS Sections
    sections = ["Manage Blog Posts", "Manage Config File"]
    choice = st.sidebar.selectbox("Choose an action", sections)

    if choice == "Manage Blog Posts":
        manage_blog_posts()
    elif choice == "Manage Config File":
        manage_config()

if __name__ == "__main__":
    main()
