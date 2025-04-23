import hashlib
import json
from SchoolProject import db, app
from SchoolProject.models import User, Grade, Admin, ScoreDetail, SchoolClass, UserEnum, Regulation
from flask_login import current_user
from sqlalchemy import func
from datetime import datetime

def add_user(name, avatar, birthday_str, gender, address, phone, email, class_id):
    try:
        # Convert birthday string to age
        birth_date = datetime.strptime(birthday_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        # Get regulations
        regulations = Regulation.query.first()
        if not regulations:
            regulations = Regulation()
            db.session.add(regulations)
            db.session.commit()
        
        # Validate age against regulations
        if age < regulations.min_age:
            raise ValueError(f"Tuổi học sinh phải từ {regulations.min_age} tuổi trở lên.")
        if age > regulations.max_age:
            raise ValueError(f"Tuổi học sinh không được quá {regulations.max_age} tuổi.")
            
        # Validate class size
        current_class_size = User.query.filter_by(class_id=class_id).count()
        if current_class_size >= regulations.max_students_per_class:
            raise ValueError(f"Lớp đã đủ {regulations.max_students_per_class} học sinh. Không thể thêm nữa.")
            
        # Create new user
        u = User(
            name=name, 
            avatar=avatar if avatar else None,
            birthday=age,  # Store the age as an integer
            gender=gender,
            address=address,
            phone=phone,
            email=email,
            class_id=class_id
        )
        db.session.add(u)
        db.session.commit()
        return True, "Thêm học sinh thành công!"
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi: {str(e)}"

def add_teacher(name, username, password, class_id=None, role=2):
    try:      
        # Hash password
        hashed_password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
        
        # Create new admin/teacher
        user = Admin(name=name, 
                    username=username, 
                    password=hashed_password,
                    role=role,
                    class_id=class_id)
        
        db.session.add(user)
        db.session.commit()
        return True, "Thêm thành công!"
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def add_score(student_id, form_data):
    try:
        # Validate
        if not all(form_data.get(field) for field in ['subject', 'semester', 'year']):
            return False, "Thiếu thông tin bắt buộc"

        # Xóa điểm cũ
        ScoreDetail.query.filter_by(
            student_id=student_id,
            subject=form_data['subject'],
            semester=form_data['semester'],
            year=form_data['year']
        ).delete()

        # Lưu điểm mới (đơn giản hóa score_type)
        def save_score(score_type_prefix, max_attempts, form_prefix):
            for i in range(1, max_attempts + 1):
                if score := form_data.get(f'{form_prefix}_{i}'):
                    db.session.add(ScoreDetail(
                        student_id=student_id,
                        subject=form_data['subject'],
                        semester=form_data['semester'],
                        year=form_data['year'],
                        score_type=f'{score_type_prefix}{i}',  # VD: '15P1' thay vì '15P_1'
                        score_value=float(score)
                    ))

        save_score('15P', 5, 'd15')  # Điểm 15 phút
        save_score('1T', 3, 'd1t')  # Điểm 1 tiết

        # Điểm cuối kỳ
        if final_score := form_data.get('final'):
            db.session.add(ScoreDetail(
                student_id=student_id,
                subject=form_data['subject'],
                semester=form_data['semester'],
                year=form_data['year'],
                score_type='FINAL',
                score_value=float(final_score)
            ))

        db.session.commit()
        return True, "Lưu điểm thành công"

    except ValueError:
        db.session.rollback()
        return False, "Điểm phải là số từ 0-10"
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi hệ thống: {str(e)}"

def get_scores_by_subject(student_id, subject, semester, year):
    return ScoreDetail.query.filter_by(
        student_id=student_id,
        subject=subject,
        semester=semester,
        year=year
    ).all()

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
    return SchoolClass.query.options(db.joinedload(SchoolClass.teacher)).get(class_id)

def auth_user(username, password):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
    return Admin.query.filter(Admin.username.__eq__(username), Admin.password.__eq__(password)).first()

def show_score(student_id):
    return ScoreDetail.query.filter_by(student_id=student_id)

def calculate_average_score(student_id, subject, semester, year):
    scores = ScoreDetail.query.filter_by(
        student_id=student_id,
        subject=subject,
        semester=semester,
        year=year
    ).all()
    
    if not scores:
        return None
        
    # Group scores by type
    score_15p = [s.score_value for s in scores if s.score_type.startswith('15P')]
    score_1t = [s.score_value for s in scores if s.score_type.startswith('1T')]
    score_final = [s.score_value for s in scores if s.score_type == 'FINAL']
    
    # Calculate weighted sum
    total_weight = 0
    weighted_sum = 0
    
    # 15 phút - hệ số 1
    if score_15p:
        avg_15p = sum(score_15p) / len(score_15p)
        weighted_sum += avg_15p * 1
        total_weight += 1
    
    # 1 tiết - hệ số 2
    if score_1t:
        avg_1t = sum(score_1t) / len(score_1t)
        weighted_sum += avg_1t * 2
        total_weight += 2
    
    # Cuối kỳ - hệ số 3
    if score_final:
        weighted_sum += score_final[0] * 3
        total_weight += 3
    
    if total_weight == 0:
        return None
        
    return round(weighted_sum / total_weight, 2)

def get_class_average_scores(class_id, subject, semester, year):
    # Get all students in the class
    students = User.query.filter_by(class_id=class_id).all()
    
    # Calculate average for each student
    averages = []
    for student in students:
        avg = calculate_average_score(student.id, subject, semester, year)
        if avg is not None:
            averages.append({
                'student_id': student.id,
                'student_name': student.name,
                'average': avg
            })
    
    # Sort by average score descending
    averages.sort(key=lambda x: x['average'], reverse=True)
    
    return averages

def get_all_classes():
    """Get all classes from the database"""
    classes = SchoolClass.query.all()
    return [{'id': c.id, 'name': c.name} for c in classes]

def check_class_exists(name):
    """Check if a class with the given name already exists"""
    return SchoolClass.query.filter_by(name=name).first() is not None

def get_class_count_by_grade(grade_id):
    """Get the number of classes in a grade"""
    return SchoolClass.query.filter_by(grade_id=grade_id).count()

def add_class(name, grade_id):
    """Add a new class"""
    class_obj = SchoolClass(name=name, grade_id=grade_id)
    db.session.add(class_obj)
    db.session.commit()

def check_last_class_in_grade(class_id):
    """Check if this is the last class in its grade"""
    class_obj = SchoolClass.query.get(class_id)
    if class_obj:
        return get_class_count_by_grade(class_obj.grade_id) <= 1
    return False

if __name__=="__main__":
    with app.app_context():
        print()