from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .models import Student, Teacher, Subj, Announcement, Material, Assignment, AssignmentFile, Quiz
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify
from website import db
from sqlalchemy.orm import joinedload
from datetime import datetime
import os
from werkzeug.utils import secure_filename

views = Blueprint('views', __name__)

UPLOAD_FOLDER = os.path.abspath('website/static/files/assignments')  # Update with the actual path
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/', methods=['GET', 'POST'])
@login_required
def home(): 
    return render_template('login.html', user=current_user)

@views.route('/student', methods=['GET', 'POST'])
@login_required
def student(): 
    # Get the currently logged-in student (assuming you have the current_user from flask-login)
    current_student = Student.query.get(current_user.id)

    return render_template('home-student.html', user=current_user, enrolled_subjects=current_student.enrolled_courses)

@views.route('/teacher', methods=['GET', 'POST'])
@login_required
def teacher():
    # Get the currently logged-in teacher (assuming you have the current_user from flask-login)
    current_teacher = Teacher.query.get(current_user.id)

    return render_template('home-teacher.html', user=current_user, teacher=current_teacher)

@views.route('/view-subject/<int:subject_id>',  methods=['GET', 'POST'])
def view_subject(subject_id):
    # Assuming you have a way to retrieve the subject information from the database
    subject = Subj.query.get(subject_id)

    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('student'))  # Redirect to a meaningful page if subject not found

    return render_template('view-subject.html', user=current_user, subject=subject)

@views.route('teacher-stream/<int:subject_id>',  methods=['GET', 'POST'])
def teacher_stream(subject_id):
    # Assuming you have a way to retrieve the subject information from the database
    subject = Subj.query.get(subject_id)

    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('student'))  # Redirect to a meaningful page if subject not found

    return render_template('teacher-stream.html', user=current_user, subject=subject)

@views.route('/teacher-classwork/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def teacher_classwork(subject_id):
    subject = Subj.query.get(subject_id)
    materials = Material.query.filter_by(subject_id=subject_id).order_by(Material.created_at.desc()).all()
    assignments = Assignment.query.filter_by(subject_id=subject_id).order_by(Assignment.created_at.desc()).all()

    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('student'))

    if request.method == 'POST':
        content_type = request.form.get('content_type')

        if content_type == 'announcement':
            announcement_title = request.form.get('announcementTitle')
            announcement_content = request.form.get('announcementContent')

            new_announcement = Announcement(
                title=announcement_title,
                content=announcement_content,
                teacher=current_user,
                subject=subject
            )
            db.session.add(new_announcement)
            db.session.commit()

            flash('Announcement created!', category='success')

        elif content_type == 'material':
            title = request.form.get('materialTitle')
            content = request.form.get('materialContent')
            file = request.files.get('materialFile')

            file_path = os.path.abspath('website/static/files/materials')  # Update with the actual path

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            if file:
                try:
                    filename = secure_filename(file.filename)
                    full_file_path = os.path.join(file_path, filename)
                    file.save(full_file_path)
                    print('File saved:', full_file_path)
                except Exception as e:
                    flash('Error while saving the file: ' + str(e), category='error')
                    filename = None
                    print('Exception while saving:', e)
            else:
                filename = None
                flash('Material creation failed! Please make sure to provide a file.', category='error')

            if filename is not None:
                new_material = Material(
                    title=title,
                    content=content,
                    file_path=filename,
                    teacher=current_user,
                    subject_id=subject_id,
                    created_at=datetime.utcnow()
                )

                db.session.add(new_material)
                db.session.commit()

                flash('Material created!', category='success')

        elif content_type == 'assignment':
            assignment_title = request.form.get('assignment_title')
            assignment_description = request.form.get('assignment_description')
            assignment_due_date = request.form.get('assignment_due_date')
            files = request.files.getlist('assignment_files[]')

            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)

            filenames = []  # List to store file names

            for file in files:
                try:
                    if file.filename == '':
                        flash('No selected file', 'error')
                        return redirect(request.url)
                    
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        full_file_path = os.path.join(UPLOAD_FOLDER, filename)
                        file.save(full_file_path)
                        filenames.append(filename)
                        flash('File uploaded successfully', 'success')
                    else:
                        flash('Invalid file format', 'error')
                except Exception as e:
                    flash('Error while saving the file: ' + str(e), 'error')
                    print('Exception while saving:', e)

            print('Filenames:', filenames)

            due_date_str = request.form.get('assignment_due_date')
            assignment_due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')

            # ... (previous code)

            if filenames:
                new_assignment = Assignment(
                title=assignment_title,
                description=assignment_description,
                due_date=assignment_due_date,
                teacher=current_user,
                subject_id=subject_id,
                created_at=datetime.utcnow()
            )
                for filename in filenames:
                    new_assignment_file = AssignmentFile(
                        file_path=filename,
                        assignment=new_assignment
                    )
                    db.session.add(new_assignment_file)

                db.session.add(new_assignment)
                db.session.commit()

                flash('Assignment created!', 'success')
                
            else:
                flash('Assignment creation failed! Please make sure to provide at least one valid file.', 'error')

        elif content_type == 'quiz':
            quiz_title = request.form.get('quizTitle')
            quiz_instructions = request.form.get('quizInstructions')
            quiz_timer = int(request.form.get('quizTimer'))
            
            # Get the number of questions you have in the form
            num_questions = int(request.form.get('numQuestions'))

            print('Quiz Title:', quiz_title)  # Debugging print
            print('Quiz Instructions:', quiz_instructions)  # Debugging print
            print('Quiz Timer:', quiz_timer)  # Debugging print
            print('Number of Questions:', num_questions)  # Debugging print

            # Collect quiz questions, options, and correct answers from the form
            quiz_questions_data = []

            for i in range(num_questions):
                question = request.form.get(f'question_{i}')
                question_type = request.form.get(f'questionType_{i}')
                options = []
                correct_answer = ''

                print(f'Question {i + 1}:', question)  # Debugging print
                print(f'Question Type {i + 1}:', question_type)  # Debugging print

                if question_type == 'multiple_choice':
                    for j in range(4):
                        option = request.form.get(f'option_{i}_{j}')
                        options.append(option)

                        print(f'Option {j + 1} for Question {i + 1}:', option)  # Debugging print

                    correct_answer = request.form.get(f'correct_{i}')

                    print(f'Correct Answer for Question {i + 1}:', correct_answer)  # Debugging print

                # Add the collected data to the quiz_questions_data list
                quiz_questions_data.append({
                    'question': question,
                    'question_type': question_type,
                    'options': options,
                    'correct_answer': correct_answer
                })

            print('Quiz Questions Data:', quiz_questions_data)  # Debugging print

            new_quiz = Quiz(
                title=quiz_title,
                instructions=quiz_instructions,
                timer=quiz_timer,
                questions=quiz_questions_data,
                teacher=current_user,
                subject_id=subject_id,
                created_at=datetime.utcnow()
            )

            db.session.add(new_quiz)

            try:
                db.session.commit()
                flash('Quiz created!', 'success')
                print('Quiz created successfully!')  # Add this print statement
            except Exception as e:
                db.session.rollback()  # Rollback in case of error
                flash('Error creating quiz: ' + str(e), 'error')
                print('Exception during database commit:', e)

    announcements = subject.announcements[::-1]
    
    for announcement in announcements:
        announcement.content_type = 'announcement'
    for material in materials:
        material.content_type = 'material'
    for assignment in assignments:
        assignment.content_type = 'assignment'


    # Combine announcements, materials, and assignments into a single list
    content_list = announcements + materials + assignments

    # Sort the combined list by creation date
    content_list.sort(key=lambda content: content.created_at, reverse=True)

    return render_template('teacher-classwork.html', user=current_user, subject=subject, content_list=content_list, subject_id=subject_id)

@views.route('/teacher-people/<int:subject_id>', methods=['GET', 'POST'])
def create_quiz():
    # Get the data from the request
    data = request.get_json()

    quiz_title = data.get('quizTitle')
    quiz_timer = data.get('quizTimer')
    quiz_data = data.get('quizData')

    # Store the quiz data in the database as needed
    # ...
    
    # Return a response (you can customize the response as needed)
    response = {
        'message': 'Quiz created successfully',
        'quizTitle': quiz_title,
        'quizTimer': quiz_timer
    }
    return jsonify(response)

def teacher_people(subject_id):
    # Assuming you have a way to retrieve the subject information from the database
    subject = Subj.query.get(subject_id)

    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('student'))  # Redirect to a meaningful page if subject not found

    # Assuming you have a way to get the list of students enrolled in this subject
    students = subject.students

    return render_template('teacher-people.html', user=current_user, subject=subject, students=students)

@views.route('/teacher-grades/<int:subject_id>',  methods=['GET', 'POST'])
def teacher_grades(subject_id):
    # Assuming you have a way to retrieve the subject information from the database
    subject = Subj.query.get(subject_id)

    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('student'))  # Redirect to a meaningful page if subject not found

    return render_template('teacher-grades.html', user=current_user, subject=subject)

@views.route('/view-announcement/<int:announcement_id>', methods=['GET'])
def view_announcement(announcement_id):
    announcement = Announcement.query.options(joinedload(Announcement.teacher)).get_or_404(announcement_id)
    return render_template('teacher-view-announcement.html', announcement=announcement, subject=announcement.subject)

@views.route('/view-material/<int:material_id>', methods=['GET'])
def view_material(material_id):
    material = Material.query.options(joinedload(Material.teacher)).get_or_404(material_id)
    return render_template('teacher-view-material.html', material=material, subject=material.subject)
