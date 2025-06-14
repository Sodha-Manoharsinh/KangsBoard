from peewee import fn
from werkzeug.security import generate_password_hash,check_password_hash
from models import User,Project
from datetime import datetime, timedelta

# to generate hashed password
def generate_hash(password):
    p = generate_password_hash(password=password)
    return p

# to check hashed password
def check_hash(hashed_password,password):
    status = check_password_hash(hashed_password,password)
    if status:
        return status
    else:
        return False
    

# to get time format or 1 hour ago, 2 days ago etc
def get_time_ago(last_seen_str):
    if not last_seen_str:
        return "Unknown"
    
    last_seen = datetime.fromisoformat(last_seen_str)
    now = datetime.utcnow()
    delta = now - last_seen

    if delta < timedelta(minutes=1):
        return "Just now"
    elif delta < timedelta(hours=1):
        mins = int(delta.total_seconds() // 60)
        return f"{mins} min ago"
    elif delta < timedelta(days=1):
        hours = int(delta.total_seconds() // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = delta.days
        return f"{days} day{'s' if days > 1 else ''} ago"

def update_all_users_total_views():
    users = User.select()
    for user in users:
        total = (Project
                 .select(fn.SUM(Project.views).alias('total'))
                 .where(Project.user == user)
                 .scalar()) or 0
        user.total_views = total
        user.save()

def increment_project_view(project_id):
    project = Project.get_or_none(Project.id == project_id)
    if project:
        project.views += 1
        project.save()

def update_user_has_project(user_id):
    user = User.get_or_none(User.id == user_id)
    if user:
        user.has_project = Project.select().where(Project.user == user).exists()
        user.save()

# def update_single_user_has_project(user_id):
#     user = User.get_or_none(User.id == user_id)
#     if user:
#         user.has_project = Project.select().where(Project.user == user).exists()
#         user.save()
