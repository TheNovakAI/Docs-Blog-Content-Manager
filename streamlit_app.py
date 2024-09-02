import streamlit as st
from github import Github
from streamlit_ace import st_ace
import json
import yaml

# Load secrets
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
REPO_NAME = "Cubs-Capital/cubsAI-SAAS"
BRANCH_NAME = "master"
BLOG_PATH = "cubsAI/blog/docs/"
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
    """List files in the GitHub repo at a given path."""
    contents = repo.get_contents(path, ref=BRANCH_NAME)
    return [file.path for file in contents if file.type == "file"]

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
    current_content = load_file_content(file_path)
    new_content = st_ace(value=current_content, language='markdown', theme='github', auto_update=True)
    
    if st.button("Save Changes"):
        update_file_content(file_path, new_content, f"Updated {file_path}")
        st.success(f"Updated {file_path} successfully!")

def manage_blog_posts():
    """Manage blog posts: add new or delete existing."""
    st.sidebar.subheader("Blog Post Management")
    blog_files = list_files_in_folder(BLOG_PATH)
    selected_blog = st.sidebar.selectbox("Select a blog post to edit", blog_files)
    
    if st.sidebar.button("Delete Selected Blog"):
        repo.delete_file(selected_blog, "Delete blog post", repo.get_contents(selected_blog).sha)
        st.success("Blog post deleted successfully.")
    
    display_editor(selected_blog)
    
    if st.sidebar.button("Add New Blog Post"):
        new_blog_name = st.sidebar.text_input("New Blog Filename", "new-blog.md")
        new_blog_content = st_ace(language='markdown', theme='github')
        
        if st.sidebar.button("Create Blog Post"):
            repo.create_file(f"{BLOG_PATH}/{new_blog_name}", "Add new blog post", new_blog_content)
            st.success(f"New blog post {new_blog_name} created successfully.")

def manage_config():
    """Manage the Astro config file to adjust sidebar and blog settings."""
    st.sidebar.subheader("Config File Management")
    config_content = load_file_content(CONFIG_PATH)
    
    # Display config content in the editor
    st.subheader("Editing Config File")
    new_config_content = st_ace(value=config_content, language='javascript', theme='github', auto_update=True)
    
    if st.button("Save Config Changes"):
        update_file_content(CONFIG_PATH, new_config_content, "Updated astro.config.mjs")
        st.success("Config file updated successfully!")
    
    # Parse and display a visual representation of the config (for example, a sidebar preview)
    config_data = yaml.safe_load(new_config_content)
    st.sidebar.markdown("### Sidebar Preview")
    display_sidebar_structure(config_data.get('integrations', []))

def display_sidebar_structure(integrations):
    """Display the sidebar structure visually from the config."""
    for integration in integrations:
        if 'starlight' in integration:
            sidebar = integration['starlight'].get('sidebar', [])
            for section in sidebar:
                st.sidebar.markdown(f"**{section['label']}**")
                for item in section['items']:
                    st.sidebar.markdown(f"- {item['label']}")

def main():
    st.title("THE Novak AI - Custom CMS")
    st.sidebar.title("CMS Navigation")

    # Authentication
    if not authenticate():
        st.stop()

    # CMS Sections
    sections = ["Manage Blog Posts", "Manage Config File"]
    choice = st.sidebar.selectbox("Choose an action", sections)

    if choice == "Manage Blog Posts":
        manage_blog_posts()
    elif choice == "Manage Config File":
        manage_config()

if __name__ == "__main__":
    main()
