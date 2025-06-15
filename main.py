from functools import wraps

from flask import Flask, render_template, redirect, request, flash, url_for, abort
from flask_bootstrap import Bootstrap5 # if you see an error saying there's no Bootstrap5, use 'pip install bootstrap-flask' directly in the terminal
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from forms import TodoForm, TodoListForm
from dotenv import load_dotenv
import os
from spreadsheet import TodoSheet, User

# Todo: add in user log in functionality with google sheets data -> when deleting things should zoom into those created by the User and not others
# todo: make the todo_list page only avail to those who are logged in
# todo: make a login and register page
# optional: add in functionality to change task list name
# add in functionality to check off and remove tasks
# add in functionality to browse all task lists
# add a way to delete tasks lists
# find a way to handle duplicates

todo_sheet = TodoSheet()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
Bootstrap5(app) # this is for WTForms otherwise have the type the bootstrap code out manually

# Set up Flask to use Flask-Login.
# This makes the 'current_user' object available in ALL templates automatically.
login_manager = LoginManager()
login_manager.init_app(app)

# Load the users
@login_manager.user_loader
def load_user(user_id):
    return todo_sheet.get_user(user_id)

# Define logged_in function
def logged_in(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            return function(*args, **kwargs)
        else:
            abort(403)
    return wrapper

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/todo_list/<string:task_list_name>", methods=["POST", "GET"])
@logged_in
def todo_list(task_list_name):
    task_list_name = task_list_name
    form = TodoForm()
    tasks = [row for row in todo_sheet.get_all_tasks() if row[1].lower() == task_list_name.lower() and row[0] == current_user.email]
    # note the checkbox value in google sheets, the TRUE is actually a String.

    if form.validate_on_submit():
        print("Form submitted")
        new_task = [current_user.email, task_list_name, form.data['task_name'], form.data['due_date'].strftime("%Y-%m-%d"), False]
        todo_sheet.add_new_task(row=new_task)
        return redirect(url_for('todo_list', task_list_name=task_list_name))
    return render_template("todo_list.html", form=form, tasks=tasks, task_list_name=task_list_name)

@app.route("/all_lists", methods=["POST", "GET"])
@logged_in
def view_lists():
    task_lists = [row for row in todo_sheet.get_all_lists() if row[1] == current_user.email]
    form = TodoListForm()
    if form.validate_on_submit():
        print("Todo List Created.")
        if form.validate_on_submit():
            row = [form.data['todo_list_name'], current_user.email]
            todo_sheet.add_new_list(row=row)
            return redirect('/all_lists')
    return render_template("all_lists.html", task_lists=task_lists, form=form)

@app.route("/completed")
@logged_in
def complete_task():
    # not recommended to use *args
    task_list_name = request.args.get("task_list_name") # use this if you are expecting this args
    task_name = request.args.get("task_name")
    due_date = request.args.get("due_date")
    all_rows = todo_sheet.get_all_tasks()

    # Get the row number -> tip: enumerate is a python function that allows you to get the index and the value at the same time
    for index, row in enumerate(all_rows):
        if row[0] == current_user.email and row[1] == task_list_name and row[2] == task_name and row[3] == due_date:
            row_number = index + 2 # + 1 because python index starts from 0 and another +1 cos of header row
            print(row_number)
            if row[-1] == 'TRUE':
                row[-1] = False
            elif row[-1] == 'FALSE':
                row[-1] = True
            todo_sheet.tasks_sheet.update(range_name=f"{row_number}:{row_number}", values=[row])
    return redirect(url_for('todo_list', task_list_name=task_list_name))

@app.route("/delete")
@logged_in
def delete_task():
    # not recommended to use *args
    task_list_name = request.args.get("task_list_name")  # use this if you are expecting this args
    task_name = request.args.get("task_name")
    due_date = request.args.get("due_date")
    all_rows = todo_sheet.get_all_tasks()

    # Get the row number -> tip: enumerate is a python function that allows you to get the index and the value at the same time
    for index, row in enumerate(all_rows):
        if row[0] == current_user.email and row[1] == task_list_name and row[2] == task_name and row[3] == due_date:
            row_number = index + 2  # + 1 because python index starts from 0 and another +1 cos of header row
            todo_sheet.tasks_sheet.delete_rows(row_number)
            print('task deleted.')
    return redirect(url_for('todo_list', task_list_name=task_list_name))

@app.route("/delete_list")
@logged_in
def delete_list():
    task_list_name = request.args.get("task_list_name")
    all_task_lists = todo_sheet.get_all_lists()
    all_tasks = todo_sheet.get_all_tasks()

    for index, row in enumerate(all_task_lists):
        if row[0] == task_list_name and row[1] == current_user.email:
            row_number = index + 2
            todo_sheet.todo_list_sheet.delete_rows(row_number)
            print(row_number)

            task_row_to_delete = []
            for task_row_number, task in enumerate(all_tasks):
                if task[1] == task_list_name and row[1] == current_user.email:
                    task_number = task_row_number + 2
                    task_row_to_delete.append(task_number)
                    # since you can't update all_tasks in the middle of a for loop, you can collect all the row numbers, then start with the largest first so the earlier rows are not affected

            for task_row in task_row_to_delete[::-1]:
                todo_sheet.tasks_sheet.delete_rows(task_row)
            print("Task list deleted.")
    return redirect(url_for('view_lists'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user_email = request.form.to_dict()["email"].lower()
        user_password = request.form.to_dict()["password"]
        # existing_user = [row for row in todo_sheet.get_all_users() if row[1] == user_email] => wrong, this returns a list of rows, we just want the user row
        user_row = next((row for row in todo_sheet.get_all_users() if row[1] == user_email), None) # returns the first matching value in the condition before the comma, else give the value after the comma
        if user_row:
            if check_password_hash(pwhash=user_row[2], password=user_password) is True:
                # convert this user_row into a USER OBJECT first before you can use login_user
                existing_user = User(id=user_row[0], email=user_row[1], password=user_row[2])
                login_user(existing_user)
                return redirect("/")
            else:
                flash("The password is incorrect. Please try again.")
        else:
            flash("That email does not exist. Please register.")
            return redirect("/register")

    return render_template("login.html")

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        user_email = request.form.to_dict()["email"]
        user_password = request.form.to_dict()["password"]
        print(user_password)
        user_row = next((row for row in todo_sheet.get_all_users() if row[1] == user_email), None)
        if user_row:
            # scalar returns just ONE value, scalars can return MULTIPLE, its a list
            flash("You've already signed up with that email, log in instead!")
            # we must also include the flash message in our template so that the message will show.
            # the 'with' keyword in jinja just creates a temporary variable, 'messages' that exists only inside that code block, and will be gone once the end of the code block is reached
            return redirect(url_for('login'))
            # instead of using url_for can also use '/login' directly
        else:
            encrypted_password = generate_password_hash(user_password, method="pbkdf2:sha256", salt_length=8)
            user_id = len(todo_sheet.get_all_users()) + 1
            new_user = [user_id, user_email, encrypted_password]
            todo_sheet.user_sheet.append_row(new_user)
            flash("User created! Please sign in.")
            return redirect("/login")

    return render_template("register.html")

@app.route("/logout")
@logged_in
def logout():
    logout_user()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)