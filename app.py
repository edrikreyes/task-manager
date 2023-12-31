from flask import Flask, render_template, request, flash, redirect, url_for
import secrets
from database import load_tasks, task_to_db, del_task, new_user, id_is_unique, \
    get_userinfo_by_username, get_username_from_id, load_tasks_by_priority
from flask_login import LoginManager, login_user, login_required, UserMixin, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from logging import FileHandler, WARNING

app = Flask(__name__, template_folder="templates")
app.secret_key = secrets.token_hex(32)
login_manager = LoginManager(app)
file_handler = FileHandler('errorlog.txt')
file_handler.setLevel(WARNING)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def get_username(self):
        return str(self.username)


@login_manager.user_loader
def load_user(user_id):
    user_info = get_username_from_id(user_id)
    if user_id:
        user = User(id=user_id, username=user_info)
        return user
    return None  # Return None if the user is not found


@app.route('/signup', methods=['POST'])
def sign_up():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        pswd = data.get('pswd')
        hash_pswd = generate_password_hash(pswd, method='pbkdf2:sha256', salt_length=16)

        if id_is_unique(username):
            new_user(username, hash_pswd)  # Adds the user's username and (hashed) pswd to DB.
            user_info = get_userinfo_by_username(username)  # Gets the users ID and username from DB.
            user = User(id=user_info['id'], username=user_info['username'])  # Creates the User object.
            login_user(user)  # Logs the user in.
            return redirect(url_for('task_page'))
        else:
            flash('Username is taken', 'error')
        return redirect(url_for('main_page'))


# @app.route('/test')
# # @login_required
# def test():
#     return 'The current user is' + current_user.get_id()

@app.route('/login', methods=['POST'])
def log_in():
    if request.method == 'POST':
        data = request.form
        username = data.get('lnusername')
        pswd = data.get('lnpswd')
        user_info = get_userinfo_by_username(username)
        if user_info is not None:
            hash_pass = user_info['pswd']
            user = User(user_info['id'], username=user_info['username'])
            if check_password_hash(pwhash=hash_pass, password=pswd):
                login_user(user)
                return redirect(url_for('task_page'))
            else:
                flash('Password is incorrect', 'error')
                return redirect(url_for('main_page'))
        else:
            flash('User not found', 'error')
            return redirect(url_for('main_page'))


@app.route('/logout', methods=['POST'])
@login_required
def log_out():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for('main_page'))


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/task-page', methods=['GET', 'POST'])
@login_required
def task_page():
    user_id = current_user.get_id()
    action = request.form.get('action')
    sort_option = request.form.get('sort_option')

    if action == 'delete':
        tsk_id = request.form.get('id')
        del_task(tsk_id)

    if sort_option == 'newest':
        tasks = load_tasks(user_id)
    elif sort_option == 'priority':
        tasks = load_tasks_by_priority(user_id)
    else:
        tasks = load_tasks(user_id)

    return render_template('task-page.html', tsk=tasks)


@app.route('/task-page/confirmed', methods=['POST'])
@login_required
def confirmed_tsk():
    data = request.form
    ui = current_user.get_id()
    if ui is not None:
        task_to_db(data, int(ui))

    return redirect(url_for('task_page'))


@app.route('/task-page/del', methods=['POST'])
@login_required
def delete_task():
    data = request.form
    tsk_id = data.get('id')
    del_task(tsk_id)
    user_id = current_user.get_id()
    tasks = load_tasks(user_id)
    return render_template('task-page.html', tsk=tasks)


if __name__ == "__main__":
    app.debug = True
    app.run()
