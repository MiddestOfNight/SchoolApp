import json
from datetime import datetime
from SchoolProject import db, app
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship
from enum import Enum as RoleEnum
from flask_login import UserMixin

class UserEnum(RoleEnum):
    ADMIN = 1
    TEACHER = 2

class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now())
    active = Column(Boolean, default=True)

    def __str__(self):
        return self.name

class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = {'extend_existing': True}
    name = Column(String(50), nullable=False, unique=True)
    classes = relationship('SchoolClass', backref='grade', lazy=True, foreign_keys='SchoolClass.grade_id')

class SchoolClass(Base):
    __tablename__ = "classes"
    __table_args__ = {'extend_existing': True}
    name = Column(String(50), nullable=False, unique=True)
    grade_id = Column(Integer, ForeignKey('grades.id'), nullable=False)
    students = relationship('User', backref='class_ref', lazy=True)
    teacher = relationship('Admin', backref='classroom', uselist=False, 
                         primaryjoin="and_(SchoolClass.id==Admin.class_id, Admin.role==2)")

    def __str__(self):
        return self.name

class User(Base):
    __tablename__ = "students"
    __table_args__ = {'extend_existing': True}
    name = Column(String(100))
    avatar = Column(String(300), default="https://i.pinimg.com/736x/f1/0f/f7/f10ff70a7155e5ab666bcdd1b45b726d.jpg")
    birthday = Column(Integer, nullable=False)
    gender = Column(String(10))
    address = Column(String(100))
    phone = Column(String(100))
    email = Column(String(100), unique=True)
    class_id = Column(Integer, ForeignKey('classes.id'))

class Admin(Base, UserMixin):
    __tablename__ = "administrators"
    __table_args__ = {'extend_existing': True}
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)
    role = Column(Integer, default=UserEnum.TEACHER.value)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=True)

    @property
    def is_admin(self):
        return self.role == UserEnum.ADMIN.value

    @property
    def is_teacher(self):
        return self.role == UserEnum.TEACHER.value

class ScoreType(RoleEnum):
    FIFTEEN_MIN = "15P"
    ONE_PERIOD = "1TIET"
    FINAL = "FINAL"

class ScoreDetail(Base):
    __tablename__ = 'score_details'
    __table_args__ = {'extend_existing': True}
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    subject = Column(String(50), nullable=False)
    semester = Column(Integer, nullable=False)
    year = Column(String(10), nullable=False)
    score_type = Column(String(10), nullable=False)
    attempt = Column(Integer)  # Thêm trường phân biệt lần nhập (1,2,3...)
    score_value = Column(Float, nullable=False)

    student = relationship('User', backref="scores")

    def to_dict(self):
        from SchoolProject.dao import calculate_average_score
        avg = calculate_average_score(
            self.student_id,
            self.subject,
            self.semester,
            self.year
        )
        return {
            'type': self.score_type,
            'value': self.score_value,
            'average': avg
        }

    @property
    def average_score(self):
        """Get the average score for this student in this subject/semester/year"""
        from SchoolProject.dao import calculate_average_score
        return calculate_average_score(
            self.student_id,
            self.subject,
            self.semester,
            self.year
        )

class Regulation(Base):
    __tablename__ = 'regulations'
    __table_args__ = {'extend_existing': True}
    min_age = Column(Integer, default=15)
    max_age = Column(Integer, default=20)
    max_students_per_class = Column(Integer, default=40)
    
    def __str__(self):
        return f"School Regulations"

class Subject(Base):
    __tablename__ = 'subjects'
    __table_args__ = {'extend_existing': True}
    name = Column(String(50), nullable=False, unique=True)

    def __str__(self):
        return self.name

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
        # # Create grades
        # g10 = Grade(name="10")
        # g11 = Grade(name="11")
        # g12 = Grade(name="12")
        # db.session.add_all([g10, g11, g12])

        # # Import students from JSON file
        # with open("data/full_class_student.json", encoding='utf-8') as f:
        #     students = json.load(f)
        #     for student in students:
        #         user = User(**student)
        #         db.session.add(user)
        #
        # # Create classes for grade 10
        # c1 = SchoolClass(name="10A1", grade_id=1)
        # c2 = SchoolClass(name="10A2", grade_id=1)
        # c3 = SchoolClass(name="10A3", grade_id=1)
        # db.session.add_all([c1, c2, c3])
        
        # Create admin user
        # import hashlib
        # admin = Admin(
        #     name="Admin",
        #     username="admin",
        #     password=str(hashlib.md5("123".encode('utf-8')).hexdigest()),
        #     role=1  # UserEnum.ADMIN.value = 1
        # )
        # db.session.add(admin)

        # Add default subjects if they don't exist
        # default_subjects = ['Toán', 'Văn', 'Anh']
        # for subject_name in default_subjects:
        #     if not Subject.query.filter_by(name=subject_name).first():
        #         subject = Subject(name=subject_name)
        #         db.session.add(subject)
        
        db.session.commit()

