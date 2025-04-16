import hashlib
import json
from SchoolProject import db, app
from SchoolProject.models import Grade, Admin, ScoreDetail
from models import User, SchoolClass, UserEnum
from flask_login import current_user
from sqlalchemy import func

def add_user(name, avatar, birthday, gender, address, phone, email, class_id):
    u = User(name=name, avatar=avatar, birthday=birthday, gender=gender, address=address, phone=phone, email=email, class_id=class_id)
    db.session.add(u)
    db.session.commit()

def add_teacher(name, username, password, class_id):
    u = Admin(
        name=name,
        username=username,
        password=str(hashlib.md5(password.encode('utf-8')).hexdigest()),
        class_id=class_id,
        role=UserEnum.TEACHER
    )
    db.session.add(u)
    db.session.commit()

def add_score(student_id, subject, semester, year, d15_scores, d1t_scores, final_score):
    for s in d15_scores:
        if s:
            detail = ScoreDetail(
                student_id=student_id,
                subject=subject,
                semester=semester,
                year=year,
                score_type='15P',
                score_value=float(s)
            )
            db.session.add(detail)

    for s in d1t_scores:
        if s:
            detail = ScoreDetail(
                student_id=student_id,
                subject=subject,
                semester=semester,
                year=year,
                score_type='1TIET',
                score_value=float(s)
            )
            db.session.add(detail)

    if final_score:
        detail = ScoreDetail(
            student_id=student_id,
            subject=subject,
            semester=semester,
            year=year,
            score_type='FINAL',
            score_value=float(final_score)
        )
        db.session.add(detail)
    db.session.commit()

def get_student_by_id(user_id):
    return User.query.get(user_id)

def get_user_by_id(user_id):
    return Admin.query.get(user_id)

def count_student():
    return User.query.count()

def count_class(class_id):
    return User.query.filter(User.class_id == class_id).count()

def load_student(q=None, class_id=None, page=None):
    query = User.query

    if q:
        query = query.filter(User.name.contains(q))
    if class_id:
        query = query.filter(User.class_id.__eq__(class_id))

    if page:
        size = app.config["PAGE_SIZE"]
        start = (int(page)-1)*size
        query = query.slice(start, start+size)

    return query.all()

def load_class(grade_id=None):
    query = SchoolClass.query
    if grade_id:
        query = query.filter(SchoolClass.grade_id.__eq__(grade_id))
    return query.all()

def load_grade():
    query = Grade.query
    return query.all()

def get_class_by_id(class_id):
    return SchoolClass.query.get(class_id)

def auth_user(username, password):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
    return Admin.query.filter(Admin.username.__eq__(username), Admin.password.__eq__(password)).first()


if __name__=="__main__":
    with app.app_context():
        print()