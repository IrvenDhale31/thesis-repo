from flask import Blueprint, flash, render_template, redirect, request, url_for, current_app
from website import db
from .models import Student, Teacher, Administrator, Subj, Announcement, Material, Assignment, AssignmentFile
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import random, string

auth = Blueprint('auth', __name__)

def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def add_admin_account():
    email = 'admin@admin.com'
    password = 'admin123456'
    given_name = 'admin'

    existing_admin = Administrator.query.filter_by(email=email).first()
    if existing_admin:
        return False
    else:
        hashed_password = generate_password_hash(password, method='sha256')
        admin = Administrator(email=email, password=hashed_password, givenName=given_name)
        db.session.add(admin)
        db.session.commit()
        login_user(admin, remember=True)
        return True

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        admin = Administrator.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password, password):
            flash('Logged in as administrator successfully!', category='success')
            login_user(admin, remember=True)
            return redirect(url_for('auth.admin'))

        student = Student.query.filter_by(email=email).first()
        if student and check_password_hash(student.password, password):
            flash('Logged in as student successfully!', category='success')
            login_user(student, remember=True)
            return redirect(url_for('views.student'))

        teacher = Teacher.query.filter_by(email=email).first()
        if teacher and check_password_hash(teacher.password, password):
            flash('Logged in as teacher successfully!', category='success')
            login_user(teacher, remember=True)
            return redirect(url_for('views.teacher'))

        flash('Incorrect email or password!', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up-student', methods=['GET', 'POST'])
def signup_student():
    if request.method == 'POST':
        studentGname = request.form.get('studentGname')
        studentLname = request.form.get('studentLname')
        studentEmail = request.form.get('studentEmail')
        studentPassword = request.form.get('studentPassword')
        studentIDNum = request.form.get('studentIDNum')

        student = Student.query.filter_by(email=studentEmail).first()
        
        if student:
            flash('Email already exists', category='error')
        elif len(studentEmail) < 4:
            flash('Email must be greater than 3 characters', category='error')
        elif len(studentGname) < 2:
            flash('Given name must be greater than 1 character', category='error')
        elif len(studentLname) < 2:
            flash('Last name must be greater than 1 character', category='error')
        elif len(studentPassword) < 7:
            flash('Last name must be at least 7 characters', category='error')
        elif len(studentIDNum) < 6:
            flash('ID number must be at least 6 digits', category='error')
        else:
            new_student = Student(givenName=studentGname, lastName=studentLname, email=studentEmail, password=generate_password_hash(studentPassword, method='sha256'), idNumber=studentIDNum)
            db.session.add(new_student)
            db.session.commit()
            login_user(new_student, remember=True)
            flash('Student account created!', category='success')
            return redirect(url_for('views.student'))
        
    return render_template("signup-student.html", user=current_user)

@auth.route('/sign-up-teacher', methods=['GET', 'POST'])
def signup_teacher():
    if request.method == 'POST':
        teacherGname = request.form.get('teacherGname')
        teacherLname = request.form.get('teacherLname')
        teacherEmail = request.form.get('teacherEmail')
        teacherPassword = request.form.get('teacherPassword')

        teacher = Teacher.query.filter_by(email=teacherEmail).first()
        if teacher:
            flash('Email already exists', category='error')
        elif len(teacherEmail) < 4:
            flash('Email must be greater than 3 characters', category='error')
        elif len(teacherGname) < 2:
            flash('Given name must be greater than 1 character', category='error')
        elif len(teacherLname) < 2:
            flash('Last name must be greater than 1 character', category='error')
        elif len(teacherPassword) < 7:
            flash('Last name must be at least 7 characters', category='error')
        else:
            new_teacher = Teacher(givenName=teacherGname, lastName=teacherLname, email=teacherEmail, password=generate_password_hash(teacherPassword, method='sha256'))
            db.session.add(new_teacher)
            db.session.commit()
            login_user(new_teacher, remember=True)
            flash('Teacher account created!', category='success')
            return redirect(url_for('views.teacher'))

    return render_template("signup-teacher.html", user=current_user)

add_admin_account()

@auth.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    subject = Subj.query.all()
    teachers = Teacher.query.all()
    students = Student.query.all()
    
    return render_template('home-admin.html', user=current_user, subject=subject, teachers=teachers, students=students)

@auth.route('/create-subject', methods=['GET', 'POST'])
def create_course():
    if request.method == 'POST':
        subjectSection = request.form.get('subjectSection')
        subjectName = request.form.get('subjectName')
        subjectCode = request.form.get('subjectCode')
        subjectTeacher_id = int(request.form.get('subjectTeacher'))  # Convert the teacher ID to an integer

        subject = Subj.query.filter_by(code=subjectCode).first()

        if subject:
            flash('Course already exists', category='error')
        else:
            # Get the teacher with the provided ID
            teacher = Teacher.query.get(subjectTeacher_id)

            if teacher is None:
                flash('Invalid teacher selected', category='error')
            else:
                new_subject = Subj(section=subjectSection, course=subjectName, code=subjectCode, invCode=generate_random_string(6))
                
                # Associate the subject with the teacher
                new_subject.teachers.append(teacher)

                db.session.add(new_subject)
                db.session.commit()
                flash('New course created!', category='success')
                return redirect(url_for('auth.admin'))

    teachers = Teacher.query.all()
    return render_template("class.html", user=current_user, teachers=teachers)

@auth.route('/del-course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def del_course(course_id):
    subject = Subj.query.get_or_404(course_id)
    
    db.session.delete(subject)
    db.session.commit()

    return redirect(url_for('auth.admin'))

@auth.route('/edit-subj/<int:course_id>', methods=['GET', 'POST'])
def edit_subj(course_id):
    subj = Subj.query.get(course_id)
    teachers = Teacher.query.all()

    if request.method == 'POST':
        subj.section = request.form['subjectSection']
        subj.course = request.form['subjectName']

        # Get the selected teacher ID from the form
        teacher_id = int(request.form['subjectTeacher'])
        # Find the corresponding Teacher object using the selected ID
        teacher = Teacher.query.get(teacher_id)

        # Set the teachers attribute directly to a new list containing the selected teacher
        subj.teachers = [teacher]

        subj.code = request.form['subjectCode']
        
        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('auth.admin'))
    
    return render_template('edit-subject.html', user=current_user, subj=subj, teachers=teachers)



@auth.route('/del-teacher/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
def del_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    
    db.session.delete(teacher)
    db.session.commit()

    return redirect(url_for('auth.admin'))

@auth.route('/create-teacher', methods=['GET', 'POST'])
def create_teacher():
    if request.method == 'POST':
        teacherGname = request.form.get('teacherGname')
        teacherLname = request.form.get('teacherLname')
        teacherEmail = request.form.get('teacherEmail')
        teacherPassword = request.form.get('teacherPassword')

        teacher = Teacher.query.filter_by(email=teacherEmail).first()
        if teacher:
            flash('Email already exists', category='error')
        elif len(teacherEmail) < 4:
            flash('Email must be greater than 3 characters', category='error')
        elif len(teacherGname) < 2:
            flash('Given name must be greater than 1 character', category='error')
        elif len(teacherLname) < 2:
            flash('Last name must be greater than 1 character', category='error')
        elif len(teacherPassword) < 7:
            flash('Last name must be at least 7 characters', category='error')
        else:
            new_teacher = Teacher(givenName=teacherGname, lastName=teacherLname, email=teacherEmail, password=generate_password_hash(teacherPassword, method='sha256'))
            db.session.add(new_teacher)
            db.session.commit()
            login_user(new_teacher, remember=True)
            flash('Teacher account created!', category='success')
            return redirect(url_for('auth.admin'))

    return render_template("teacher.html", user=current_user)

@auth.route('/del-student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def del_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    db.session.delete(student)
    db.session.commit()

    return redirect(url_for('auth.admin'))

@auth.route('/create-student', methods=['GET', 'POST'])
def create_student():
    if request.method == 'POST':
        studentGname = request.form.get('studentGname')
        studentLname = request.form.get('studentLname')
        studentEmail = request.form.get('studentEmail')
        studentPassword = request.form.get('studentPassword')
        studentIDNum = request.form.get('studentIDNum')

        student = Student.query.filter_by(email=studentEmail).first()
        if student:
            flash('Email already exists', category='error')
        elif len(studentEmail) < 4:
            flash('Email must be greater than 3 characters', category='error')
        elif len(studentGname) < 2:
            flash('Given name must be greater than 1 character', category='error')
        elif len(studentLname) < 2:
            flash('Last name must be greater than 1 character', category='error')
        elif len(studentPassword) < 7:
            flash('Last name must be at least 7 characters', category='error')
        else:
            new_student = Student(givenName=studentGname, lastName=studentLname, email=studentEmail, password=generate_password_hash(studentPassword, method='sha256'), idNumber=studentIDNum)
            db.session.add(new_student)
            db.session.commit()
            login_user(new_student, remember=True)
            flash('Student account created!', category='success')
            return redirect(url_for('auth.admin'))

    return render_template("student.html", user=current_user)

@auth.route('/edit-student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get(student_id)

    if request.method == 'POST':
        student.email = request.form['studentEmail']
        student.password = request.form['studentPassword']
        student.givenName = request.form['studentGname']
        student.lastName = request.form['studentLname']
        student.idNumber = request.form['studentIDNum']
        
        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('auth.admin'))

    return render_template('edit-student.html', user=current_user, student=student)

@auth.route('/edit-teacher/<int:teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    teacher = Teacher.query.get(teacher_id)

    if request.method == 'POST':
        teacher.email = request.form['teacherEmail']
        teacher.password = request.form['teacherPassword']
        teacher.givenName = request.form['teacherGname']
        teacher.lastName = request.form['teacherLname']

        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('auth.admin'))

    return render_template('edit-teacher.html', user=current_user, teacher=teacher)

from flask import request, flash

@auth.route('/enroll-student/<int:student_id>', methods=['GET', 'POST'])
def enroll_student(student_id):
    student = Student.query.get(student_id)
    subject = Subj.query.all()

    if request.method == 'POST':
        enrolled_course_id = int(request.form.get('enrolledCourse'))
        enrolled_course = Subj.query.get(enrolled_course_id)

        if enrolled_course:
            # Check if the student is already enrolled in the selected course
            if enrolled_course in student.enrolled_courses:
                flash('Student is already enrolled in this course', category='error')
            else:
                # Enroll the student in the selected course
                student.enrolled_courses.append(enrolled_course)

                # Save the changes to the database
                db.session.commit()

                flash('Student enrolled in the course successfully!', category='success')
                return redirect(url_for('auth.admin'))
        else:
            flash('Invalid course selected', category='error')
    
    return render_template('enroll-student.html', user=current_user, student=student, subject=subject)

@auth.route('/unenroll-student/<int:student_id>', methods=['GET', 'POST'])
def unenroll_student(student_id):
    student = Student.query.get(student_id)
    subject = Subj.query.all()

    if request.method == 'POST':
        unenroll_course_id = int(request.form.get('enrolledCourse'))
        unenroll_course = Subj.query.get(unenroll_course_id)

        if unenroll_course:
            # Check if the student is enrolled in the selected course
            if unenroll_course in student.enrolled_courses:
                # Unenroll the student from the selected course
                student.enrolled_courses.remove(unenroll_course)

                # Save the changes to the database
                db.session.commit()

                flash('Student unenrolled from the course successfully!', category='success')
                return redirect(url_for('auth.admin'))
            else:
                flash('Student is not enrolled in this course', category='error')
        else:
            flash('Invalid course selected', category='error')
    
    return render_template('unenroll-student.html', user=current_user, student=student, subject=subject)

@auth.route('/enroll', methods=['GET', 'POST'])
def enroll():
    if request.method == 'POST':
        subj_code = request.form['subjCode']

        # Query the database to find the subject with the given invitation code
        subj = Subj.query.filter_by(invCode=subj_code).first()

        if subj:
            # Check if the student is already enrolled in the subject
            if current_user in subj.students:
                flash('You are already enrolled in this subject.', 'info')
            else:
                # Enroll the student in the subject
                subj.students.append(current_user)
                db.session.commit()
                flash('Enrolled in the subject successfully!', 'success')
                return render_template('home-student.html', user=current_user)
        else:
            flash('Invalid invitation code. Please try again.', 'error')

    return render_template("enroll.html", user=current_user)

@auth.route('/del-announcement/<int:announcement_id>', methods=['POST', 'GET'])
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    subject_id = announcement.subject_id

    db.session.delete(announcement)
    db.session.commit()

    flash('Announcement deleted successfully!', 'success')
    return redirect(url_for('views.teacher_classwork', subject_id=subject_id))

@auth.route('/edit-announcement/<int:announcement_id>', methods=['GET', 'POST'])
@login_required
def edit_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)

    if request.method == 'POST':
        new_title = request.form.get('new_title')
        new_content = request.form.get('new_content')

        # Update the announcement with the new title and content
        announcement.title = new_title
        announcement.content = new_content
        db.session.commit()

        flash('Announcement updated successfully!', 'success')
        return redirect(url_for('views.teacher_classwork', subject_id=announcement.subject_id))

    return render_template('edit_announcement.html', announcement=announcement)

@auth.route('/edit-material/<int:material_id>', methods=['GET', 'POST'])
@login_required
def edit_material(material_id):
    material = Material.query.get_or_404(material_id)

    if request.method == 'POST':
        new_title = request.form.get('new_title')
        new_content = request.form.get('new_content')

        # Update the material with the new title and content
        material.title = new_title
        material.content = new_content
        db.session.commit()

        flash('Material updated successfully!', 'success')
        return redirect(url_for('views.teacher_classwork', subject_id=material.subject_id))

    return render_template('edit_material.html', material=material)


@auth.route('/del-material/<int:material_id>', methods=['POST', 'GET'])
def delete_material(material_id):
    material = Material.query.get_or_404(material_id)
    subject_id = material.subject_id

    db.session.delete(material)
    db.session.commit()

    return redirect(url_for('views.teacher_classwork', subject_id=subject_id))

@auth.route('/del-assignment/<int:assignment_id>', methods=['POST', 'GET'])
def delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    subject_id = assignment.subject_id

    # Delete the associated assignment files
    for file in assignment.files:
        try:
            # Remove the file from the file system if needed
            # Delete the corresponding AssignmentFile record
            db.session.delete(file)
        except Exception as e:
            # Handle errors
            print(f"Error while deleting file: {e}")

    # Delete the assignment
    db.session.delete(assignment)
    db.session.commit()

    return redirect(url_for('views.teacher_classwork', subject_id=subject_id))