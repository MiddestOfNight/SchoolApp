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

class SchoolClass(Base):
    __tablename__ = "classes"
    __table_args__ = {'extend_existing': True}
    name = Column(String(50), nullable=False, unique=True)
    grade_id = Column(Integer, ForeignKey(Grade.id))

class User(Base):
    __tablename__ = "students"
    __table_args__ = {'extend_existing': True}
    name = Column(String(100))
    avatar = Column(String(300), default="https://res.cloudinary.com/dy1unykph/image/upload/v1740037805/apple-iphone-16-pro-natural-titanium_lcnlu2.webp")
    birthday = Column(Integer, nullable=False)
    gender = Column(String(10))
    address = Column(String(100))
    phone = Column(String(100))
    email = Column(String(100), unique=True)
    class_id = Column(Integer, ForeignKey(SchoolClass.id))

class Admin(Base, UserMixin):
    __tablename__ = "administrators"
    __table_args__ = {'extend_existing': True}
    name = Column(String(100))
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)
    role = Column(Enum(UserEnum), default=UserEnum.TEACHER)
    class_id = Column(Integer, ForeignKey(SchoolClass.id), nullable=True, unique=True)

    classroom = relationship(SchoolClass, backref="teacher", uselist=False)

class ScoreDetail(Base):
    __tablename__ = 'score_details'
    __table_args__ = {'extend_existing': True}
    student_id = Column(Integer, ForeignKey(User.id), nullable=False)
    subject = Column(String(50), nullable=False)
    semester = Column(Integer, nullable=False)
    year = Column(String(10), nullable=False)
    score_type = Column(Enum('15P', '1TIET', 'FINAL', name='score_type_enum'), nullable=False)
    score_value = Column(Float, nullable=False)

    student = relationship(User, backref="scores")

if __name__ =="__main__":
    with app.app_context():
        db.create_all()
        # c1 = Grade(name="10")
        # c2 = Grade(name="11")
        # c3 = Grade(name="12")
        # db.session.add_all([c1, c2, c3])
        # c4 = SchoolClass(name="10A1", grade_id=1)
        # c5 = SchoolClass(name="10A2", grade_id=1)
        # c6 = SchoolClass(name="10A3", grade_id=1)
        #
        #
        # db.session.add_all([c4, c5, c6])

        # with open("data/full_class_student.json", encoding='utf-8') as f:
        #     students = json.load(f)
        #     for p in students:
        #         prod = User(**p)
        #         db.session.add(prod)

        # import hashlib
        # u = Admin(name="teacher2", username="user11", password=str(hashlib.md5("123".encode('utf-8')).hexdigest()), role=UserEnum.TEACHER, class_id=1)
        # u2 = Admin(name="Admin1", username="admin", password=str(hashlib.md5("123".encode('utf-8')).hexdigest()),role=UserEnum.ADMIN)
        # db.session.add(u)
        # db.session.add(u2)
        db.session.commit()

