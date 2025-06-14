# operations.py

from peewee import IntegrityError
from models import Project, User

def add_project_db(user_id, title, description, github_link, host_link, technologies):
    user = User.get_or_none(User.id == user_id)
    if not user:
        return "Unauthorized", "danger", False

    try:
        Project.create(
            user=user,
            title=title,
            description=description,
            github_link=github_link,
            host_link=host_link,
            technologies=technologies,
            views=0
        )
        return "Project added successfully!", "success", True
    except IntegrityError:
        return "Project with this GitHub or Host link already exists.", "danger", False


def update_project_db(user_id, project_id, title, description, github_link, host_link, technologies):
    user = User.get_or_none(User.id == user_id)
    project = Project.get_or_none(Project.id == project_id, Project.user == user)
    if not project:
        return "Project not found.", "danger", False

    try:
        project.title = title
        project.description = description
        project.github_link = github_link
        project.host_link = host_link
        project.technologies = technologies
        project.save()
        return "Project updated successfully!", "success", True
    except IntegrityError:
        return "Update failed: GitHub or Host link must be unique.", "danger", False


def delete_project_db(user_id, project_id):
    user = User.get_or_none(User.id == user_id)
    project = Project.get_or_none(Project.id == project_id, Project.user == user)
    if project:
        project.delete_instance()
        return "Project deleted successfully.", "info"
    else:
        return "Project not found or unauthorized.", "danger"
