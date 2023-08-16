from website import db
from flask_login import UserMixin
from datetime import datetime  # Import the datetime module
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime

# Association table for the many-to-many relationship between Teacher and Subject
teacher_subject_association = db.Table('teacher_subject_association',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subj.id'), primary_key=True)
)

student_course_association = db.Table('student_course_association',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('subj.id'), primary_key=True)
)

class Student(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    givenName = db.Column(db.String(150))
    lastName = db.Column(db.String(150))
    idNumber = db.Column(db.Integer, unique=True)

    # Define the relationship with the Subject model
    enrolled_courses = db.relationship('Subj', secondary=student_course_association, backref=db.backref('students', lazy='dynamic'))

class Teacher(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    givenName = db.Column(db.String(150))
    lastName = db.Column(db.String(150))

    # Define the relationship with the Subject model
    subjects = db.relationship('Subj', secondary=teacher_subject_association, backref=db.backref('teachers', lazy='dynamic'))
    quiz_relationship = db.relationship('Quiz', back_populates='teacher')  # Add this line

class Administrator(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    givenName = db.Column(db.String(150))

class Subj(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(150))
    course = db.Column(db.String(150))
    code = db.Column(db.String(150), unique=True)
    invCode = db.Column(db.String(150), unique=True)
    quiz_relationship = db.relationship('Quiz', back_populates='subject')  # Add this line

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    teacher = db.relationship('Teacher', backref=db.backref('announcements', lazy=True))

    subject_id = db.Column(db.Integer, db.ForeignKey('subj.id'), nullable=False)
    subject = db.relationship('Subj', backref=db.backref('announcements', lazy=True))

    def __repr__(self):
        return f"<Announcement(id={self.id}, title='{self.title}', subject_id={self.subject_id}, teacher_id={self.teacher_id})>"
    
class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255))  # Store the file path
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    teacher = db.relationship('Teacher', backref=db.backref('materials', lazy=True))

    subject_id = db.Column(db.Integer, db.ForeignKey('subj.id'), nullable=False)
    subject = db.relationship('Subj', backref=db.backref('materials', lazy=True))

    def __repr__(self):
        return f"<Material(id={self.id}, title='{self.title}', subject_id={self.subject_id}, teacher_id={self.teacher_id})>"
    
class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    teacher = db.relationship('Teacher', backref=db.backref('assignments', lazy=True))

    subject_id = db.Column(db.Integer, db.ForeignKey('subj.id'), nullable=False)
    subject = db.relationship('Subj', backref=db.backref('assignments', lazy=True))

    files = db.relationship('AssignmentFile', backref='assignment', lazy=True)  # Relationship for multiple files
    assignment_files = relationship('AssignmentFile', backref='assignment_ref')  # Changed the backref name

    def __repr__(self):
        return f"<Assignment(id={self.id}, title='{self.title}', subject_id={self.subject_id}, teacher_id={self.teacher_id})>"

class AssignmentFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), nullable=False)

    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)

# Define the association table for the many-to-many relationship between Quiz and Subj (Subject)
quiz_subject_association = db.Table('quiz_subject_association',
    db.Column('quiz_id', db.Integer, db.ForeignKey('quiz.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subj.id'), primary_key=True)
)

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    instructions = Column(String(1000))
    timer = Column(Integer, nullable=False)  # Timer in minutes
    questions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    teacher_id = Column(Integer, ForeignKey('teacher.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subj.id'), nullable=False)

    teacher = relationship("Teacher", back_populates="quiz_relationship")  # Update here
    subject = relationship("Subj", back_populates="quiz_relationship")  # Update here
