import peewee
from utils import generate_hash,check_hash
from models import User

def signup_db(username,email,password):
    try:
        hashed_pass = generate_hash(password)
        User.create(username=username,email=email,password=hashed_pass)
        message,category,status = "Sign Up is successful.",'success',True
        return message,category,status
    except peewee.IntegrityError :
        message,category,status = "Username or Email already exists.",'danger',False
        return message,category,status
    
def login_db(username, password):
    user = User.get_or_none(User.username == username)
    if user:
        if check_hash(user.password, password):
            message, category, status = "Login successful.", 'success', True
            return message, category, status, user

    message, category, status = "Invalid details.", 'danger', False
    return message, category, status, None
