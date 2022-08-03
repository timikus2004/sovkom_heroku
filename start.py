from collections import namedtuple
from xml.dom.pulldom import ErrorHandler

from flask import Flask, render_template, request,redirect, url_for,flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import check_password_hash,generate_password_hash


app = Flask(__name__)

ENV = 'dev'

if ENV == 'dev':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://timikus:password@localhost/myapp'
    app.debug = True
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://lchvtkoztfyvnt:9f1ff8fe29d951cb27a821bcee40882863a224b3636b316f47a769b4d264852c@ec2-3-213-228-206.compute-1.amazonaws.com:5432/d3ann4ba97q4s9'
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


if __name__ == '__main__':
    app.run()