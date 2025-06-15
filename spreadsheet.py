from dotenv import load_dotenv
import gspread, json, os
from gspread_formatting import DataValidationRule, BooleanCondition, set_data_validation_for_cell_range
from google.oauth2.service_account import Credentials

from flask_login import UserMixin

# todo: create the user class
# todo: set up the load_user correctly somehow

class User(UserMixin):
    def __init__(self, id, email, password):
        super().__init__()
        self.id = id
        self.email = email
        self.password = password

class TodoSheet:
    def __init__(self):
        load_dotenv()
        # Read and parse the env var
        creds_dict = json.loads(os.environ.get("GSHEET_CREDS_JSON"))
        creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive'])
        # scopes lets it know which service can access, in this case giving it google sheets read/write access, also need google drive access to search for the gsheet file

        gc = gspread.authorize(creds)
        # gc = gspread.service_account(filename='./creds/Exercise Tracker Bot.json')
        sh = gc.open("Task List Database")
        # Get the spreadsheet
        self.tasks_sheet = sh.sheet1
        self.todo_list_sheet = sh.worksheet("Task Lists")
        self.set_up_checkbox()
        self.user_sheet = sh.worksheet("Users")

    def set_up_checkbox(self):
        # Create the checkbox rule
        checkbox_rule = DataValidationRule(
            condition=BooleanCondition('BOOLEAN'),
            showCustomUi=True
        )

        # Apply it to a range (e.g. C2:C100 for checkbox column)
        set_data_validation_for_cell_range(self.tasks_sheet, 'E2:E', checkbox_rule)

    def add_new_task(self, row):
        # row = ["User 1", "Task List 1", "Submit AORB", "2025-06-11", False]
        self.tasks_sheet.append_row(row)

    def get_all_tasks(self):
        data_rows = self.tasks_sheet.get_all_values()[1:]
        return data_rows

    def add_new_list(self, row):
        self.todo_list_sheet.append_row(row)

    def get_all_lists(self):
        data_rows = self.todo_list_sheet.get_all_values()[1:]
        return data_rows

    def get_user(self, user_id):
        all_users = self.user_sheet.get_all_values()[1:]
        for row in all_users:
            if row[0] == user_id:
                selected_user = User(id=user_id, email=row[1], password=row[2])
                # we decide what the user_id is
                return selected_user

    def get_all_users(self):
        return self.user_sheet.get_all_values()[1:]