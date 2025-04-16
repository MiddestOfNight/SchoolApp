import hashlib
import math

from flask import render_template, request, redirect, session, jsonify
import dao
from flask_login import login_user, current_user, logout_user, login_required
import cloudinary.uploader

from SchoolProject import app, login
from datetime import datetime

from SchoolProject.models import Admin, UserEnum


def calculate_age(birthday_str):
    # Convert the string to a datetime object
    birth_date = datetime.strptime(birthday_str, "%Y-%m-%d").date()
    today = datetime.today().date()

    # Calculate age
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

@app.route('/')
def index():
    grades = dao.load_grade()
    return render_template("index.html", grades=grades)

@app.route('/grade/<int:grade_id>')
def class1(grade_id):
    classes = dao.load_class(grade_id=grade_id)
    return render_template("class.html", classes=classes, grade_id=grade_id)


@app.route('/grade/<int:grade_id>/class/<int:id>')
def inclass(grade_id, id):
    q = request.args.get("q")
    page = request.args.get("page", 1, type=int)
    ccount = dao.count_class(class_id=id)
    students = dao.load_student(q=q, class_id=id, page=page)
    clazz = dao.get_class_by_id(id)
    classes = dao.load_class(grade_id=grade_id)
    return render_template("inclass.html", classes=classes,
                           students=students,
                           pages=int(math.ceil(dao.count_student() / app.config["PAGE_SIZE"])),
                           ccount=ccount,
                           clazz=clazz,
                           grade_id=grade_id)

@app.route('/student/<int:id>')
def details(id):
    stu = dao.get_student_by_id(id)
    return render_template('student_details.html', stu=stu)

@login.user_loader
def get_user(user_id):
    return dao.get_user_by_id(user_id=user_id)

@app.route('/get-classes')
def get_classes():
    grade_id = request.args.get('grade_id')
    classes = dao.load_class(grade_id=grade_id)
    return jsonify([{'id': c.id, 'name': c.name} for c in classes])

@app.route("/registerstudent", methods=['GET','POST'])
def registerstudent():
    err_msg = None
    success_msg = None
    if request.method == "POST":
        try:
            name = request.form.get('name')
            avatar = request.files.get('avatar')
            path = None
            if avatar:
                res = cloudinary.uploader.upload(avatar)
                path = res['secure_url']
            birthday_str = request.form.get('birthday')
            age = calculate_age(birthday_str)
            if age < 15 or age > 20:
                raise ValueError("Tuổi học sinh phải từ 15 đến 20.")
            gender = request.form.get('gender')
            address = request.form.get('address')
            phone = request.form.get('phone')
            email = request.form.get('email')
            if '@' not in email:
                raise ValueError("Email không hợp lệ. Vui lòng nhập địa chỉ có dấu @.")
            class_id = request.form.get('class_id')
            if not class_id:
                raise ValueError("Vui lòng chọn lớp cho học sinh.")
            current_count = dao.count_class(class_id)
            if current_count >= 40:
                raise ValueError("Lớp đã đủ 40 học sinh. Không thể thêm nữa.")
            dao.add_user(name, path, birthday, gender, address, phone, email, class_id)
            success_msg = "Thêm thành công!"
        except Exception as e:
            err_msg = f"Lỗi: {str(e)}"
    grades = dao.load_grade()
    return render_template('register_student.html', err_msg=err_msg, success_msg=success_msg, grades=grades)

@app.route("/registerteacher", methods=['GET', 'POST'])
@login_required  # Chỉ cho admin
def register_teacher():
    err_msg = None
    success_msg = None

    if request.method == "POST":
        try:
            name = request.form.get('name')
            username = request.form.get('username')
            password = request.form.get('password')
            class_id = request.form.get('class_id')
            class_id = int(class_id) if class_id else None

            if Admin.query.filter_by(username=username).first():
                raise Exception("Tên đăng nhập đã tồn tại!")

            if Admin.query.filter_by(class_id=class_id).first():
                raise Exception("Lớp này đã được phân cho một giáo viên khác!")

            dao.add_teacher(name, username, password, class_id)

            success_msg = "Thêm giáo viên thành công!"
        except Exception as e:
            err_msg = f"Lỗi: {str(e)}"

    classes = dao.load_class()
    used_class_ids = [c.class_id for c in Admin.query.filter(Admin.class_id.isnot(None)).all()]
    return render_template("register_admin.html", classes=classes, used_class_ids=used_class_ids,
                           err_msg=err_msg, success_msg=success_msg)

@app.route('/login', methods=['get', 'post'])
def login_my_user():
    if current_user.is_authenticated:
        return redirect('/')

    err_msg = None
    next = None
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        hashed_password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()

        admin = Admin.query.filter_by(username=username.strip(), password=hashed_password).first()

        if admin:
            login_user(admin)
            next = request.args.get('next')
            return redirect(next if next else '/')
        else:
            err_msg = "Tài khoản hoặc mật khẩu không khớp!"

    return render_template('login.html', err_msg=err_msg)

@app.route('/teacher/class-list')
@login_required
def teacher_class_list():
    clazz = dao.get_class_by_id(current_user.class_id)
    students = dao.load_student(class_id=current_user.class_id)
    return render_template('teacher_class.html', clazz=clazz, students=students)

@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect('/login')

from flask import request, render_template, redirect
from flask_login import login_required, current_user
from SchoolProject import app, db
from SchoolProject.models import User, ScoreDetail
from datetime import datetime

@app.route("/teacher/score/add/<int:student_id>", methods=["GET", "POST"])
@login_required
def add_score_for_student(student_id):
    student = User.query.get_or_404(student_id)

    if request.method == "POST":
        subject = request.form.get("subject")
        semester = int(request.form.get("semester"))
        year = request.form.get("year")

        # Lấy điểm 15 phút từ form
        d15_scores = []
        for i in range(5):
            val = request.form.get(f"d15_{i}")
            d15_scores.append(val if val else None)

        # Lấy điểm 1 tiết từ form
        d1t_scores = []
        for i in range(3):
            val = request.form.get(f"d1t_{i}")
            d1t_scores.append(val if val else None)

        # Lấy điểm cuối kỳ
        final_score = request.form.get("final")

        # Gọi hàm DAO để lưu
        dao.add_score(student_id, subject, semester, year, d15_scores, d1t_scores, final_score)

        return render_template("add_score_single.html", student=student, message="Đã lưu điểm thành công!")

    return render_template("add_score_single.html", student=student)


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
