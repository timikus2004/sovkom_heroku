from ast import operator
from collections import namedtuple
from datetime import date, datetime

from flask import Flask, make_response, render_template, request,redirect, url_for,flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash,generate_password_hash

from config import LOCALHOST_URI, HEROKU_URI, SECRET_KEY


app = Flask(__name__)

ENV = 'prod'

if ENV == 'dev':
    app.config['SQLALCHEMY_DATABASE_URI'] = LOCALHOST_URI
    app.debug = True
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = HEROKU_URI
    app.debug = False

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']= SECRET_KEY

db = SQLAlchemy(app)

login_manager = LoginManager(app=app)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(25), unique=True)
    password = db.Column('password', db.String(255))

    def __init__(self,username,password):
        self.username = username
        self.password = password

class Operator(db.Model):
    __tablename__ = 'operators'
    id = db.Column('id', db.Integer, primary_key=True)
    op_name = db.Column('op_name', db.String(30), unique=True)
    requests = db.relationship('Request', backref=db.backref('operators', lazy=True))

    def __init__(self,op_name):
        self.op_name = op_name

class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column('id', db.Integer, primary_key=True)
    request_id = db.Column('request_id', db.Integer, unique=True, nullable=False)
    contract_id = db.Column('contract_id', db.Integer, unique=True, nullable=False)
    created = db.Column('created', db.DateTime, nullable=False, default=datetime.now)
    status = db.Column('status', db.Boolean)
    checked = db.Column('checked', db.Boolean)
    operator_id = db.Column('operator_id', db.Integer, db.ForeignKey('operators.id'), nullable=False)

    def __init__(self, request_id, contract_id, status, checked, operator_id):
        self.request_id = request_id
        self.contract_id = contract_id
        self.status = status
        self.checked = checked
        self.operator_id = operator_id
        
class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column('id', db.Integer, primary_key = True)
    examinator = db.Column('examinator', db.String(25), nullable=False)
    created = db.Column('created', db.DateTime, nullable=False, default=datetime.now)
    status = db.Column('status', db.String(25), nullable=False)
    op_decision = db.Column('op_decision', db.String(25))
    request_id = db.Column('requests_id', db.Integer, db.ForeignKey('requests.id'), nullable=False)

    def __init__(self,examinator,created,status,op_decision,request_id):
        self.examinator = examinator
        self.created = created
        self.status = status 
        self.op_decision = op_decision
        self.request_id = request_id


@app.route('/')
def index():
    if 'logged' in session:
        user = session.get('username')
        return render_template('index.html', username = user)
    return render_template('index.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if session.get('logged'):
        flash('Вы уже вошли в аккаунт')
        return redirect(url_for('index'))
    if request.method == 'POST':
        usrname = request.form.get('username')
        password = request.form.get('password')
        result = User.query.filter_by(username=usrname).first()
        if not result:
            flash('Пожалуйста зарегистрируйтесь')
            return redirect(url_for('register'))
        if result and check_password_hash(result.password, password):
            login_user(result)
            flash('Вы вошли в аккаунт')
            session['logged'] = 'logged'
            session['username'] = usrname
            return redirect(url_for('index'))
        else:
            flash('Не правильно введён пароль')
            return redirect(url_for('login'))
    return render_template('login.html')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session['logged'] = None
    session['username'] = None
    flash('Вы вышли из аккаунта')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        usrname = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if password != password2:
            flash('Пароли не совпадают!')
            return redirect(url_for('register'))
        result = User.query.filter_by(username=usrname).count()
        if result == 0 and password.__eq__(password2):
            gen_pass = generate_password_hash(password)
            add_user = User(username=usrname,password=gen_pass)
            db.session.add(add_user)
            db.session.commit()
            flash('Регистрация прошла успешно, ввойдите в аккаунт')
            return redirect(url_for('login'))
        else:
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))
    return render_template('register.html')


@app.route('/choose', methods=['GET','POST'])
@login_required
def choose():
    operators = Operator.query.all()
    if request.method == 'POST':
        operator = request.form.get('operators')
        if operator and operator != 'Список операторов:':
            response = make_response(redirect(url_for('reqlist_pag',page_num=1)))
            response.set_cookie('operator',operator)
            return response
        else:
            flash("Выберите оператора")
            return render_template('choose_operator.html',operators=operators)
        
    return render_template('choose_operator.html',operators=operators)

    
@app.route('/reqlist/<int:page_num>', methods=['GET','POST'])
@login_required
def reqlist_pag(page_num): 
    operator_name = request.cookies.get('operator')
    op_id = Operator.query.filter_by(op_name = operator_name).first().id
    data = Request.query.filter_by(operator_id=op_id).paginate(per_page=10,page = page_num)
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        data = Request.query.filter_by(operator_id=op_id).filter(Request.created >= start_date).paginate(per_page=10,page=page_num)
        print(f'pagination post: {data.total}')
        if data.pages == 0:
            flash('C введенной даты заявок не было, введите другую дату')
        return render_template('list_of_requests.html',data = data, operator=operator_name)

    return render_template('list_of_requests.html',data = data, operator=operator_name)
    

@app.route('/showreq/<int:id>', methods=['GET','POST'])
@login_required
def showreq(id):
    error = ''
    if request.method == 'POST':
        examinator = current_user.username
        decision = request.form.get('exams')
        status = 'checked'
        if decision:
            created = datetime.now()
            ex = Exam(examinator=examinator, created=created, status=status, op_decision=decision, request_id=id)
            db.session.add(ex)
            db.session.commit()
            flash('Данные успешно добавлены')
        else:
            error = "Выберите решение по оператору из выпадающего списка"
            return render_template('request.html',data=info, error=error)

    info = Request.query.get(id)
    result = Exam.query.filter_by(request_id = id).all()[-1] # to do with multiple results
    return render_template('request.html',data=info, data2 = result)
    # return 'success'


@app.errorhandler(401)
def unauthorized(error):
    message = 'Вы не авторизованы'
    return render_template('error.html', msg=message, title='Ошибка авторизации')

@app.errorhandler(404)
def not_found(error):
    message = 'Страница не найдена'
    return render_template('error.html', msg=message, title='Страница не найдена')


if __name__ == '__main__':
    app.run()
