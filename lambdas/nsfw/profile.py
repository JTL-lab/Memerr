import re
import hashlib
import datetime
from dateutil.relativedelta import relativedelta

class UserCreds:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    @property
    def password(self):
        raise AttributeError("Password is not accessible")

    @password.setter
    def password(self, raw_password):
        if len(raw_password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self._password = self._hash_password(raw_password)

    @staticmethod
    def _hash_password(password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return hashlib.sha256(password.encode()).hexdigest()


class Profile:
    def __init__(self, email, phone, username, password, date_of_birth):
        if not self._is_valid_email(email):
            raise ValueError("Invalid email format")
        self.email = email
        self.phone = phone
        self.user_creds = UserCreds(username, password)
        self.date_of_birth = date_of_birth

    @staticmethod
    def _is_valid_email(email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None


    @staticmethod
    def calculate_age(date_of_birth):
        # date_of_birth Format: "YYYY-MM-DD"
        birth_date = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d")
        today = datetime.datetime.now()
        age = relativedelta(today, birth_date).years
        return age
