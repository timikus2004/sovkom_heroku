from collections import namedtuple
from datetime import datetime

from flask import Flask, make_response, render_template, request,redirect, url_for,flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import check_password_hash,generate_password_hash


app = Flask(__name__)

ENV = 'prod'

if ENV == 'dev':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://timikus:password@localhost/myapp'
    app.debug = True
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://rvkvqakqvuuths:0dbef51e9fac3b9c8278d561e66a14cbfa51b2c566127cd99d425917f528291b@ec2-44-205-112-253.compute-1.amazonaws.com:5432/d4u1t5hsfvs1ll'
    app.debug = False

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']= '8630513a082cef10a197111db08c7217d685af2e62204bbe'

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
    created = db.Column('created', db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column('status', db.Boolean)
    checked = db.Column('checked', db.Boolean)
    operator_id = db.Column('operator_id', db.Integer, db.ForeignKey('operators.id'), nullable=False)

    def __init__(self, request_id, contract_id, status, checked, operator_id):
        self.request_id = request_id
        self.contract_id = contract_id
        self.status = status
        self.checked = checked
        self.operator_id = operator_id
        
        
@login_manager.user_loader
def load_user(user_id):
    print(f'load user id : {user_id}')
    return User.query.get(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        usrname = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if password != password2:
            flash('passwords are not equal')
            return redirect(url_for('register'))
        result = User.query.filter_by(username=usrname).count()
        if result == 0 and password.__eq__(password2):
            gen_pass = generate_password_hash(password)
            add_user = User(username=usrname,password=gen_pass)
            db.session.add(add_user)
            db.session.commit()
            flash('[INFO]: registered succesfully, enter your credentials')
            return redirect(url_for('login'))
        else:
            flash('[INFO]: user exists')
            return redirect(url_for('register'))
    return render_template('register.html')



@app.route('/login', methods=['GET','POST'])
def login():
    # error = ''
    if session.get('logged'):
        flash('[INFO]: already logged in')
        return redirect(url_for('index'))
    if request.method == 'POST':
        usrname = request.form.get('username')
        password = request.form.get('password')
        result = User.query.filter_by(username=usrname).first()
        if result and check_password_hash(result.password, password):
            login_user(result)
            flash('[INFO]: logging...')
            session['logged'] = 'logged'
            return redirect(url_for('index',hello=usrname))
        else:
            # error = '[ERROR]: Please register'
            flash('Please register')
            return redirect(url_for('register'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session['logged'] = None
    flash('[INFO]: logged out')
    return redirect(url_for('index'))

@app.errorhandler(401)
def unauthorized(error):
    message = 'you are not logged in'
    return render_template('error.html', msg=message, title='401 error')

@app.route('/choose', methods=['GET','POST'])
@login_required
def choose():
    operators = Operator.query.all()
    if request.method == 'POST':
        operator = request.form.get('operators')
        if operator:
            response = make_response(redirect(url_for('reqlist')))
            response.set_cookie('operator',operator)
            return response
        
    return render_template('choose_operator.html',operators=operators)

@app.route('/reqlist', methods=['GET','POST'])
@login_required
def reqlist():
    operator_name = request.cookies.get('operator')
    op_id = Operator.query.filter_by(op_name = operator_name).first().id
    data = Request.query.filter_by(operator_id=op_id).paginate(per_page=10)
    
    return render_template('list_of_requests.html', data = data, operator = operator_name)
    
@app.route('/reqlist/<int:page_num>', methods=['GET','POST'])
@login_required
def reqlist_pag(page_num):  
    operator_name = request.cookies.get('operator')
    op_id = Operator.query.filter_by(op_name = operator_name).first().id
    data = Request.query.filter_by(operator_id=op_id).paginate(per_page=10, page = page_num)
    return render_template('list_of_requests.html',data = data, operator=operator_name)
    
    

@app.route('/showreq/<int:id>')
@login_required
def showreq(id):
    result = Request.query.get(id)
    # print(result)
    return render_template('request.html',data=result)
    # return 'success'

if __name__ == '__main__':
    app.run()