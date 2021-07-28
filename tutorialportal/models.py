from tutorialportal import db, login_manager
from utcnow import utcnow
from flask_login import UserMixin


@login_manager.user_loader
def load_user(username):
    return User.query.get(username)


class User(db.Model, UserMixin):
    username = db.Column(db.String(25), primary_key=True)
    password = db.Column(db.String(60), nullable=False)
    admin = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return 'User({}, {})'.format(self.username, self.admin)

    def get_id(self):
        return self.username


class Admin(db.Model):
    username = db.Column(db.String(25), db.ForeignKey('user.username'), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    remark = db.Column(db.Text)

    def __repr__(self):
        return 'Admin({}, {})'.format(self.username, self.name)


class Student(db.Model):
    username = db.Column(db.String(25), db.ForeignKey('user.username'), primary_key=True)
    name = db.Column(db.String(50))
    s_phone = db.Column(db.String(8))
    p_phone = db.Column(db.String(8))
    p_rel = db.Column(db.String(20))
    lesson_day = db.Column(db.String(30), nullable=False)
    lesson_time = db.Column(db.String(5), nullable=False)
    lesson_duration = db.Column(db.String(5), nullable=False)
    lesson_fee = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    remark = db.Column(db.Text)

    def __repr__(self):
        return 'Student({}, {})'.format(self.username, self.name)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), db.ForeignKey('student.username'), nullable=False)
    dt_attendance = db.Column(db.DateTime, nullable=False, default=utcnow.get())
    lesson_date = db.Column(db.String(10), nullable=False)
    lesson_time = db.Column(db.String(5), nullable=False)
    lesson_duration = db.Column(db.String(5), nullable=False)
    lesson_fee = db.Column(db.Float, nullable=False)
    remark = db.Column(db.Text)

    def __repr__(self):
        return 'Attendance({}, {}, {})'.format(self.id, self.username, self.dt_lesson)


class FeeSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), db.ForeignKey('student.username'), nullable=False)
    dt_submission = db.Column(db.DateTime, nullable=False, default=utcnow.get())
    amount = db.Column(db.Float, nullable=False)
    remark = db.Column(db.Text)

    def __repr__(self):
        return 'FeeSubmission({}, {}, {})'.format(self.id, self.username, self.dt_submission)