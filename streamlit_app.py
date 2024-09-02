import streamlit as st
from github import Github
import os
import yaml
import markdown
from streamlit_ace import st_ace

# Load secrets
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = "Cubs-Capital/cubsAI-SAAS"  # Replace with your actual GitHub repo
BRANCH_NAME = "main"  # The branch you want to work with

# Initialize GitHub client
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def list_files_in_repo(path):
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
        update_file_content(file_path, new_content)
        st.success(f"Updated {file_path} successfully!")

def manage_blog_posts():
    """Manage blog posts: add new or delete existing."""
    st.sidebar.subheader("Blog Post Management")
    blog_files = list_files_in_repo("src/content/blog")
    selected_blog = st.sidebar.selectbox("Select a blog post to edit", blog_files)
    
    if st.sidebar.button("Delete Selected Blog"):
        repo.delete_file(selected_blog, "Delete blog post", repo.get_contents(selected_blog).sha)
        st.success("Blog post deleted successfully.")
    
    display_editor(selected_blog)
    
    if st.sidebar.button("Add New Blog Post"):
        new_blog_name = st.sidebar.text_input("New Blog Filename", "new-blog.md")
        new_blog_content = st_ace(language='markdown', theme='github')
        
        if st.sidebar.button("Create Blog Post"):
            repo.create_file(f"src/content/blog/{new_blog_name}", "Add new blog post", new_blog_content)
            st.success(f"New blog post {new_blog_name} created successfully.")

def manage_docs():
    """Manage docs content: edit files in the docs folder."""
    st.sidebar.subheader("Docs Management")
    doc_files = list_files_in_repo("src/content/docs")
    selected_doc = st.sidebar.selectbox("Select a doc file to edit", doc_files)
    display_editor(selected_doc)

def manage_sidebar_structure():
    """Manage the sidebar structure by editing the config file."""
    st.sidebar.subheader("Sidebar Management")
    config_file_path = "astro.config.mjs"
    display_editor(config_file_path)

def main():
    st.title("THE Novak AI - Custom CMS")
    st.sidebar.title("CMS Navigation")

    # CMS Sections
    sections = ["Manage Blog Posts", "Manage Docs", "Edit Sidebar Structure"]
    choice = st.sidebar.selectbox("Choose an action", sections)

    if choice == "Manage Blog Posts":
        manage_blog_posts()
    elif choice == "Manage Docs":
        manage_docs()
    elif choice == "Edit Sidebar Structure":
        manage_sidebar_structure()

if __name__ == "__main__":
    main()
