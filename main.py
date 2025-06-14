from flask import Flask, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash
from datetime import datetime
from functools import wraps
from operations import add_project_db,update_project_db,delete_project_db
from utils import get_time_ago,increment_project_view,update_user_has_project
from auth import signup_db, login_db
from models import User, Project
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = "Kangaroos"


load_dotenv()
ADMIN_SECRET = str(os.getenv("ADMIN_SECRET_KEY"))


# it is used to pass context
@app.context_processor
def utility_functions():
    return dict(get_time_ago=get_time_ago)


# Login required Decorator 
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Routes 

# ROOT
@app.route("/")
def root():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# SIGNUP
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        message, category, status = signup_db(username=username, email=email, password=password)
        flash(message, category)

        return redirect(url_for("login" if status else "signup"))
    return render_template("signup.html")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        message, category, status, user = login_db(username, password)
        flash(message, category)

        if status:
            session["user_id"] = user.id
            user.isOnline = True
            user.save()
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))
    return render_template("login.html")

# LOGOUT
@app.route("/logout")
@login_required
def logout():
    user_id = session.get("user_id")
    user = User.get_or_none(User.id == user_id)
    if user:
        user.isOnline = False
        user.last_seen = datetime.utcnow().isoformat()
        user.save()
    session.clear()
    flash("You have been logged out!", "info")
    return redirect(url_for("login"))

# DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    user = User.get_or_none(User.id == session["user_id"])
    return render_template("dashboard.html", user=user)

# EDIT PROFILE
@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    user = User.get_or_none(User.id == session["user_id"])
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form.get("password")
        skills = request.form.get("skills")
        description = request.form.get("user_description")

        if new_password:
            user.password = generate_password_hash(new_password)
        if skills:
            user.skills = skills
        if description:
            user.user_description = description

        user.save()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_profile.html", user=user)

# DELETE PROFILE
@app.route("/delete-profile")
@login_required
def delete_profile():
    user = User.get_or_none(User.id == session["user_id"])
    if user:
        user.delete_instance(recursive=True)
    session.clear()
    flash("Your profile has been deleted.", "info")
    return redirect(url_for("login"))

# ADD PROJECT
@app.route("/add-project", methods=["GET", "POST"])
@login_required
def add_project():
    user_id = session.get("user_id")
    user = User.get_or_none(User.id == user_id)

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        github_link = request.form["github_link"]
        host_link = request.form.get("host_link")
        technologies = request.form["technologies"]

        message, category, status = add_project_db(user_id, title, description, github_link, host_link, technologies)
        flash(message, category)
        if status:
            update_user_has_project(user_id=user_id)
            return redirect(url_for("dashboard"))

    return render_template("projects/add_project.html", user=user)

# UPDATE PROJECT
@app.route("/update-project/<int:project_id>", methods=["GET", "POST"])
@login_required
def update_project(project_id):
    user_id = session.get("user_id")
    user = User.get_or_none(User.id == user_id)

    project = Project.get_or_none(Project.id == project_id, Project.user == user)

    if not project:
        flash("Project not found.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        github_link = request.form["github_link"]
        host_link = request.form.get("host_link")
        technologies = request.form["technologies"]

        message, category, status = update_project_db(
            user_id, project_id, title, description, github_link, host_link, technologies
        )
        flash(message, category)
        if status:
            return redirect(url_for("dashboard"))

    return render_template("projects/update_project.html", project=project, user=user)

# DELETE PROJECT
@app.route("/delete-project/<int:project_id>", methods=["GET","POST"])
@login_required
def delete_project(project_id):
    user_id = session.get("user_id")
    message, category = delete_project_db(user_id, project_id)
    update_user_has_project(user_id=user_id)
    flash(message, category)
    return redirect(url_for("dashboard"))

# All users
@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    search_query = request.form.get("search", "")
    logged_in_user = User.get_by_id(session["user_id"])

    all_users = User.select().where(User.id != logged_in_user.id)

    if search_query:
        all_users = all_users.where(User.username.contains(search_query))

    users_with_projects = [u for u in all_users if u.has_project]
    users_with_projects.sort(key=lambda u: u.total_views, reverse=True)
    users_without_projects = [u for u in all_users if not u.has_project]

    return render_template(
        "users/users.html",
        users_with_projects=users_with_projects,
        users_without_projects=users_without_projects,
        search_query=search_query,
        user=logged_in_user,
    )

# click on users project
@app.route('/user/<int:user_id>/projects')
@login_required
def user_project(user_id):
    user = User.get_or_none(User.id == user_id)
    if not user:
        flash("User not found", "warning")
        return redirect(url_for("users"))

    if user.id != session["user_id"]:
        user.total_views += 1
        user.save()

    return render_template("users/user_projects.html", user=user)

@app.route('/project/<int:project_id>/visit/github')
@login_required
def visit_github(project_id):
    project = Project.get_or_none(Project.id == project_id)
    if not project:
        flash("Project not found", "warning")
        return redirect(url_for("dashboard"))

    increment_project_view(project.id)
    return redirect(project.github_link)

@app.route('/project/<int:project_id>/visit/host')
@login_required
def visit_host(project_id):
    project = Project.get_or_none(Project.id == project_id)
    if not project or not project.host_link:
        flash("Live link not available", "warning")
        return redirect(url_for("dashboard"))

    increment_project_view(project.id)
    return redirect(project.host_link)

@app.route("/projects", methods=["GET", "POST"])
def explore_projects():
    search_query = request.form.get("search", "")
    selected_skill = request.form.get("skill", "")

    query = Project.select().join(User)

    if search_query:
        query = query.where(Project.title.contains(search_query))

    if selected_skill:
        query = query.where(Project.technologies.contains(selected_skill))

    query = query.order_by(Project.views.desc())

    all_skills = set()
    for project in Project.select():
        if project.technologies:
            all_skills.update([s.strip() for s in project.technologies.split(",")])

    return render_template(
        "projects/explore_projects.html",
        projects=query,
        search_query=search_query,
        selected_skill=selected_skill,
        all_skills=sorted(all_skills)
    )

# View own profile
@app.route("/profile")
@login_required
def profile():
    user = User.get_or_none(User.id == session["user_id"])
    if not user:
        return redirect(url_for("login"))

    project_count = Project.select().where(Project.user == user).count()
    return render_template("profile.html", user=user, project_count=project_count)

@app.route('/kang_admin_8971_secret', methods=['GET','POST'])
def secret_admin():
    key = request.form.get("key") 
    if key != ADMIN_SECRET:
        return "Unauthorized", 403

    users = User.select()
    projects = Project.select()
    return render_template("admin.html", users=users, projects=projects)


@app.route('/admin/delete-user/<int:user_id>')
def admin_delete_user(user_id):
    secret_key = request.args.get('key')
    if secret_key != "myUltraSecretKey987":
        return "Unauthorized", 403

    user = User.get_or_none(User.id == user_id)
    if user:
        user.delete_instance(recursive=True)
        flash("User deleted", "info")
    return redirect(url_for('secret_admin', key=secret_key))

@app.route('/admin/delete-project/<int:project_id>')
def admin_delete_project(project_id):
    secret_key = request.args.get('key')
    if secret_key != "myUltraSecretKey987":
        return "Unauthorized", 403

    project = Project.get_or_none(Project.id == project_id)
    if project:
        project.delete_instance()
        flash("Project deleted", "info")
    return redirect(url_for('secret_admin', key=secret_key))

# Run 

if __name__ == "__main__":
    app.run()
