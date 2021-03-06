from flask import Blueprint, abort, flash, request, redirect, render_template, url_for
from flask_login import current_user, login_required

from tutorialportal import db, bcrypt
from tutorialportal.tutors.student_manager.forms import AddStudentForm, StudentCredentialsForm, AddAttendanceForm, \
    AddPaymentForm
from tutorialportal.models import Student, User, Attendance, FeeSubmission
from tutorialportal.config import site_en
from tutorialportal.tutors.student_manager.utils import get_highlight_count, get_all_invoice_items, day_dictionary, \
    convert_days, day_list

import datetime
import random

tutors_student_manager = Blueprint('tutors_student_manager', __name__)


@tutors_student_manager.route('/manager/student', methods=['POST', 'GET'])
@tutors_student_manager.route('/manager/student_<string:page>', methods=['POST', 'GET'])
@login_required
def student_manager(page=None):
    if current_user.tutor is False:
        abort(403)
    active_students = [(student_record.username, student_record.name) for student_record in
                       Student.query.filter_by(tutor_username=current_user.username) if student_record.active]
    inactive_students = [(student_record.username, student_record.name) for student_record in
                         Student.query.filter_by(tutor_username=current_user.username) if not student_record.active]
    add_student_form = AddStudentForm()
    panel_active = {
        'add_student': False,
        'select_student': False
    }
    if page and page in panel_active.keys():
        panel_active[page] = True
    if request.method == 'GET' and page is None:
        panel_active['select_student'] = True
    if add_student_form.add_student_submit.data:
        if add_student_form.validate_on_submit():
            username = add_student_form.name.data.split(" ")[0].lower() + datetime.datetime.now().strftime('%S%M%H')
            while User.query.get(username) is not None:
                username = add_student_form.name.data.split(" ")[0].lower() + datetime.datetime.now().strftime('%S%M%H')
            password = add_student_form.name.data.replace(" ", "") + str(random.randint(10, 100))
            user = User(username=username, password=bcrypt.generate_password_hash(password).decode('utf-8'),
                        tutor=False)
            db.session.add(user)
            input_lesson_time = add_student_form.lesson_time.data
            student = Student(username=username, name=add_student_form.name.data, s_phone=add_student_form.s_phone.data,
                              p_phone=add_student_form.p_phone.data, p_rel=add_student_form.p_rel.data,
                              lesson_day=','.join(convert_days(add_student_form.lesson_day.data)),
                              lesson_time=input_lesson_time if len(
                                  input_lesson_time) == 5 else \
                                  input_lesson_time[:2] + ':' + input_lesson_time[2:] \
                                      if ':' not in input_lesson_time else '0' + input_lesson_time
                              , lesson_duration=add_student_form.lesson_duration.data,
                              lesson_fee=add_student_form.lesson_fee.data, remark=add_student_form.remarks.data,
                              tutor_username=current_user.username, active=True)
            db.session.add(student)
            db.session.commit()
            flash('ADD Success: Student \nUsername: {}\nPassword: {}'.format(username, password), 'success')
            return redirect(url_for('tutors_student_manager.student_manager', student_username=username))
        if page is None:
            panel_active['add_student'] = True
    return render_template('tutors/student_manager.html', page_name='Student Manager',
                           add_student_form=add_student_form,
                           site=site_en, panel_active=panel_active, active_students=active_students,
                           inactive_students=inactive_students)


@tutors_student_manager.route('/manager/student/<string:student_username>', methods=['POST', 'GET'])
@tutors_student_manager.route('/manager/student/<string:student_username>/<string:page>', methods=['POST', 'GET'])
@login_required
def student_manager_selected(student_username, page=None):
    if current_user.tutor is False:
        abort(403)
    # Credentials Form, Add Attendance Form,
    # Add Payment Form, Attendance Table with controls, Payment History with controls
    panel_active = {
        'credentials': False,
        'attendance': False,
        'payment': False
    }
    if page and page in panel_active.keys():
        panel_active[page] = True
    student = Student.query.filter_by(username=student_username).first_or_404()
    if student.tutor_username != current_user.username:
        abort(403)
    if request.method == 'GET' and page is None:
        if student.active is False:
            panel_active['credentials'] = True
        else:
            panel_active['attendance'] = True
    student_credentials_form = StudentCredentialsForm()
    add_attendance_form = AddAttendanceForm()
    add_payment_form = AddPaymentForm()
    if student_credentials_form.student_credentials_submit.data:
        if student_credentials_form.validate_on_submit():
            student.name = student_credentials_form.name.data
            student.s_phone = student_credentials_form.s_phone.data
            student.p_phone = student_credentials_form.p_phone.data
            student.p_rel = student_credentials_form.p_rel.data
            student.lesson_day = ','.join(convert_days(student_credentials_form.lesson_day.data))
            input_lesson_time = student_credentials_form.lesson_time.data
            student.lesson_time = input_lesson_time if len(
                input_lesson_time) == 5 else \
                input_lesson_time[:2] + ':' + input_lesson_time[2:] \
                    if ':' not in input_lesson_time else '0' + input_lesson_time
            student.lesson_duration = student_credentials_form.lesson_duration.data
            student.lesson_fee = student_credentials_form.lesson_fee.data
            student.remark = student_credentials_form.remarks.data
            db.session.commit()
            flash('UPDATE Success: Credentials ({}).'.format(student.name), 'success')
        else:
            flash('Some of your input may be invalid.', 'danger')
        if page is None:
            panel_active['credentials'] = True
    elif add_attendance_form.add_attendance_submit.data:
        if add_attendance_form.validate_on_submit():
            # Possibly add a check in timeslot overlapping
            input_lesson_time = add_attendance_form.lesson_time.data
            attendance = Attendance(username=student.username, lesson_date=add_attendance_form.lesson_date.data,
                                    lesson_time=input_lesson_time if len(
                                        input_lesson_time) == 5 else input_lesson_time[:2] + ':' + input_lesson_time[2:]
                                    if ':' not in input_lesson_time else '0' + input_lesson_time,
                                    lesson_fee=add_attendance_form.lesson_fee.data,
                                    lesson_duration=add_attendance_form.lesson_duration.data,
                                    remark=add_attendance_form.remarks.data)
            db.session.add(attendance)
            db.session.commit()
            flash('ADD Success: Attendance ({} {}) added for {}.'.format(add_attendance_form.lesson_date.data,
                                                                         add_attendance_form.lesson_time.data,
                                                                         student.name),
                  'success')
        else:
            flash('Some of your input may be invalid.', 'danger')
        panel_active['attendance'] = True
    elif add_payment_form.add_payment_submit.data:
        if add_payment_form.validate_on_submit():
            payment = FeeSubmission(username=student_username, submission_date=add_payment_form.submission_date.data,
                                    amount=add_payment_form.amount.data, remark=add_payment_form.remarks.data)
            db.session.add(payment)
            db.session.commit()
            flash('ADD Success: Payment ({} ${}) added for {}.'.format(add_payment_form.submission_date.data,
                                                                       add_payment_form.amount.data,
                                                                       student.name),
                  'success')
        else:
            flash('Some of your input may be invalid.', 'danger')
        panel_active['payment'] = True
    student_credentials_form.name.data = student.name
    student_credentials_form.s_phone.data = student.s_phone
    student_credentials_form.p_phone.data = student.p_phone
    student_credentials_form.p_rel.data = student.p_rel
    student_credentials_form.lesson_day.data = ','.join([day_list[int(i)] for i in student.lesson_day.split(',')])
    student_credentials_form.lesson_time.data = student.lesson_time
    student_credentials_form.lesson_duration.data = student.lesson_duration
    student_credentials_form.lesson_fee.data = student.lesson_fee
    student_credentials_form.remarks.data = student.remark
    add_attendance_form.lesson_time.data = student.lesson_time
    add_attendance_form.lesson_duration.data = student.lesson_duration
    add_attendance_form.lesson_fee.data = student.lesson_fee
    add_payment_form.amount.data = student.lesson_fee
    # Student Attendance Record
    page_num_a = request.args.get('ap', 1, type=int)
    page_num_p = request.args.get('pp', 1, type=int)
    student_attendance = Attendance.query.filter_by(username=student.username).order_by(
        Attendance.lesson_date.desc()).paginate(page=page_num_a, per_page=5)
    student_payment = FeeSubmission.query.filter_by(username=student.username).order_by(
        FeeSubmission.submission_date.desc()).paginate(page=page_num_p, per_page=5)
    return render_template('tutors/student_manager_selected.html', page_name='Student Manager', site=site_en,
                           panel_active=panel_active, student=student,
                           student_credentials_form=student_credentials_form,
                           add_attendance_form=add_attendance_form, add_payment_form=add_payment_form,
                           student_attendance=student_attendance, student_payment=student_payment,
                           highlight_count=get_highlight_count(student.username, page=page_num_a),
                           all_invoice_items=get_all_invoice_items(student_username))


@tutors_student_manager.route('/make_inactive/<string:student_username>')
@login_required
def make_inactive(student_username):
    if current_user.tutor is False:
        abort(403)
    student = Student.query.get(student_username)
    if student.tutor_username != current_user.username:
        abort(403)
    if student:
        student.active = False
        db.session.commit()
        flash('SET INACTIVE Success: Student {}'.format(student.name), 'success')
        return redirect(
            url_for('tutors_student_manager.student_manager_selected', student_username=student_username,
                    page='credentials'))
    abort(403)


@tutors_student_manager.route('/make_active/<string:student_username>')
@login_required
def make_active(student_username):
    if current_user.tutor is False:
        abort(403)
    student = Student.query.get(student_username)
    if student.tutor_username != current_user.username:
        abort(403)
    if student:
        student.active = True
        db.session.commit()
        flash('SET ACTIVE Success: Student ({})'.format(student.name), 'success')
        return redirect(
            url_for('tutors_student_manager.student_manager_selected', student_username=student_username,
                    page='credentials'))
    abort(403)


@tutors_student_manager.route('/remove/student/<string:student_username>', methods=['POST'])
@login_required
def remove_student(student_username):
    if current_user.tutor is False:
        abort(403)
    student = Student.query.get(student_username)
    user = User.query.get(student_username)
    attendance = Attendance.query.filter_by(username=student_username).all()
    payment = FeeSubmission.query.filter_by(username=student_username).all()
    if student:
        if student.tutor_username != current_user.username:
            abort(403)
        name = student.name
        db.session.delete(student)
        db.session.delete(user)
        for record in attendance:
            db.session.delete(record)
        for record in payment:
            db.session.delete(record)
        db.session.commit()
        flash('DELETE Success: Student ({})'.format(name), 'success')
        return redirect(url_for('tutors_student_manager.student_manager'))
    abort(403)


@tutors_student_manager.route('/remove/attendance/<string:attendance_id>', methods=['POST'])
@login_required
def remove_attendance(attendance_id):
    if current_user.tutor is False:
        abort(403)
    attendance = Attendance.query.filter_by(id=attendance_id).first_or_404()
    student = Student.query.get(attendance.username)
    if student:
        if student.tutor_username != current_user.username:
            abort(403)
        date = attendance.lesson_date
        time = attendance.lesson_time
        db.session.delete(attendance)
        db.session.commit()
        flash('DELETE Success: Attendance ({} {}) of {}'.format(date, time, student.name), 'success')
        return redirect(url_for('tutors_student_manager.student_manager_selected', page='attendance',
                                student_username=student.username))
    abort(403)


@tutors_student_manager.route('/remove/payment/<string:payment_id>', methods=['POST'])
@login_required
def remove_payment(payment_id):
    if current_user.tutor is False:
        abort(403)
    payment = FeeSubmission.query.filter_by(id=payment_id).first_or_404()
    student = Student.query.get(payment.username)
    if student:
        if student.tutor_username != current_user.username:
            abort(403)
        date = payment.submission_date
        amount = payment.amount
        db.session.delete(payment)
        db.session.commit()
        flash('DELETE Success: Payment ({} ${}) of {}'.format(date, amount, student.name), 'success')
        return redirect(url_for('tutors_student_manager.student_manager_selected', page='payment',
                                student_username=student.username))
    abort(403)
