from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import cloudinary

app = Flask(__name__)

app.secret_key = "%$@%^@%#222^VGHGD"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456@localhost/schooldb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

app.config["PAGE_SIZE"] = 8

db = SQLAlchemy(app)
login = LoginManager(app)

# Thêm bảo vệ CSRF
csrf = CSRFProtect(app)

cloudinary.config(cloud_name='durvuy8zh',
    api_key='437287972251261',
    api_secret='rZumWoYdYnMxeBxfsNkIAJkNoHs')