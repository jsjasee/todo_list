from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, SubmitField, URLField, BooleanField
from wtforms.validators import DataRequired, URL, InputRequired, ValidationError
from wtforms.fields import DateField
from spreadsheet import TodoSheet

class TodoForm(FlaskForm):
    task_name = StringField('Enter the task you need to complete', validators=[DataRequired()])
    due_date = DateField("Due date of task", format="%Y-%m-%d")
    submit = SubmitField("Add task")

    def validate_task_name(self, field): # must name the function to be validate_<name_of_field_to_validate>
        all_task_rows_by_user = [row for row in TodoSheet().get_all_tasks() if row[0] == current_user.email]
        all_tasks = [row[2] for row in all_task_rows_by_user]
        if field.data in all_tasks:
            raise ValidationError("This task already exists.")

class TodoListForm(FlaskForm):
    todo_list_name = StringField('Give it a name', validators=[DataRequired()])
    submit = SubmitField("Create")

    def validate_todo_list_name(self, field): # must name the function to be validate_<name_of_field_to_validate>
        all_lists_rows_by_user = [row for row in TodoSheet().get_all_lists() if row[1] == current_user.email]
        all_lists_names = [row[0] for row in all_lists_rows_by_user]
        if field.data in all_lists_names:
            raise ValidationError("This todo list already exists.")