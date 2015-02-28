from flask import Flask, session, render_template, request, redirect, g, flash
from flask_login import login_required, login_user, logout_user, current_user, LoginManager
from passlib.handlers.md5_crypt import md5_crypt
from pony.orm import sql_debug, db_session
from datetime import datetime

app = Flask(__name__, instance_relative_config=False)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

from models import *

sql_debug(False)
db.generate_mapping(create_tables=True)

def testdata():
  db.drop_all_tables(with_all_data=True)
  db.create_tables()
  with db_session:
      from test_data import TestData
      test = TestData()
      test.create_members()
      test.test_settings()
      #test.datetime_test()

#testdata()

app.wsgi_app = db_session(app.wsgi_app)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"
login_manager.login_message = None

from models.User import User
from services.user_service import UserService


@login_manager.user_loader
def get_user(id):
  service = UserService()
  user = service.get(_id=id)
  if user:
    return User(user_id=id, name=user.name, email=user.email, roles=user.roles.split(","))
  return None


@app.before_request
def set_user_on_request_g():
  setattr(g, 'user', current_user)


@app.route("/")
@login_required
def home():
  return render_template('home.jinja2')

@app.route("/collection")
@login_required
def collection():
  return render_template('collection.jinja2')

@app.route("/basic_setup")
@login_required
def basic_setup():
  return render_template("basic_setup.jinja2")

@app.route("/settings")
@login_required
def settings():
  return render_template("settings.jinja2")

@app.route("/system_setup")
@login_required
def system_setup():
  return render_template("system_setup.jinja2")

@app.route("/member")
@login_required
def member():
  return render_template("member.jinja2")

@app.route("/data_reset")
@login_required
def data_reset():
  return render_template("data_reset.jinja2")

@app.route("/user", methods=['GET', 'POST'])
@login_required
def manage_user():
  service = UserService()
  user = User(user_id="",name="")
  if request.method == 'POST':
    id = request.form["id"]
    name = request.form["name"]
    password = request.form["password"]
    if id and int(id) and name:
      if password and len(password) > 4:
        password = md5_crypt.encrypt(password)
        if service.update(id, name, password):
          flash("User update successfully!")
      else:
        flash("Password should be greater than 4 letters!")
    else:
      flash("Invalid user id.")

  user_list = service.search()
  return render_template("manage_user.jinja2", user=user, user_list=user_list)

@app.route("/factory_reset")
@login_required
def factory_reset():
  create_default_users()
  return render_template("factory_reset.jinja2")

def create_default_users():
  user_service = UserService()
  user_service.add("basic", "$1$yWq10SD.$WQlvdj6kmHOY9KjHhuIGn1", "basic@milkpos.in", ["basic"], current_user.id)
  user_service.add("setup", "$1$Ii9Edtkd$cpxJMzTgpCmFxEhka2nKs/", "setup@milkpos.in", ["setup"], current_user.id)
  user_service.add("support", "$1$P/A0YAOn$O8SuzMiowBVJAorhfY239/", "support@milkpos.in", ["support"], current_user.id)
  user_service.add("admin", "$1$doG2/gED$vTLr/Iob7T9z0.nydnJxD1", "admin@milkpos.in", ["admin"], current_user.id)

@app.context_processor
def settings_provider():
    from configuration_manager import ConfigurationManager
    config_manager = ConfigurationManager()
    settings = config_manager.get_all_settings()

    d = datetime.now().strftime("%d/%m/%Y")
    t = datetime.now().strftime("%I:%M%p")

    return dict(settings=settings, date=d, time=t)

@app.route("/login", methods=['GET', 'POST'])
def login():
  service = UserService()
  username = service.get(1).name
  if request.method == 'POST':
      username = request.form["username"]
      password = request.form["password"]
      if username and password and len(password) > 4:
        service = UserService()
        users = service.search(name=username)
        if users and len(users) == 1 and md5_crypt.verify(password, users[0].password):
          dbuser = users[0]
          user = User(user_id=dbuser.id, name=dbuser.name, email=dbuser.email, roles=dbuser.roles.split(","))
          login_user(user, remember=False)
          return redirect("/")
      flash("Invalid username or password!")
  return render_template('login.jinja2', username=username)


@app.route('/logout')
@app.route('/logout/')
def app_logout():
  logout_user()
  session.clear()
  return redirect('/')