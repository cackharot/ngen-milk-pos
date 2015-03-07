from flask import Flask, session, render_template, request, redirect, g, flash, current_app, jsonify
from flask import make_response, Response
from flask_login import login_required, login_user, logout_user, current_user, LoginManager
from flask.ext.principal import Principal, Permission, RoleNeed, UserNeed
from flask.ext.principal import identity_changed, identity_loaded, Identity, PermissionDenied

from passlib.handlers.md5_crypt import md5_crypt
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from flask.ext.babel import Babel


app = Flask(__name__, instance_relative_config=False)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db' #?check_same_thread=False
app.config['SQLALCHEMY_ECHO'] = False
db = SQLAlchemy(app)

# localization
babel = Babel(app)

# authorization
principals = Principal(app)

# Create a permission with a single Need, in this case a RoleNeed.
basic_permission = Permission(RoleNeed('basic'))
setup_permission = Permission(RoleNeed('setup'))
support_permission = Permission(RoleNeed('support'))
admin_permission = Permission(RoleNeed('admin'))

from services.user_service import UserService
from models import *


def fmtDecimal(value):
  if isinstance(value, float):
    return float("{0:.2f}".format(value))
  return value


login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"
login_manager.login_message = None

from models.User import User
from configuration_manager import ConfigurationManager

@app.errorhandler(PermissionDenied)
def handle_invalid_usage(error):
    return render_template("unauthorized.jinja2"), 403

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role))

@babel.localeselector
def get_locale():
  return g.get('current_lang', 'ta')

@login_manager.user_loader
def get_user(id):
  service = UserService()
  user = service.get(_id=id)
  if user:
    u = User(user_id=id, name=user.name, email=user.email, roles=user.roles.split(","))
    print u.roles
    return u
  return None


@app.before_request
def set_user_on_request_g():
  config_manager = ConfigurationManager()
  settings = config_manager.get_all_settings()
  setattr(g, 'user', current_user)
  setattr(g, 'app_settings', settings)
  setattr(g, 'current_lang', settings.get(SystemSettings.LANGUAGE, "en"))


@app.context_processor
def settings_provider():
    settings = g.app_settings

    d = datetime.now().strftime("%d/%m/%Y")
    t = datetime.now().strftime("%I:%M%p")

    return dict(settings=settings, sys_date=d, sys_time=t)


@app.route("/")
@login_required
def home():
  return render_template('home.jinja2')


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
          # Tell Flask-Principal the identity changed
          identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))
          return redirect("/")
      flash("Invalid username or password!")
  return render_template('login.jinja2', username=username)


@app.route('/logout')
@app.route('/logout/')
def app_logout():
  logout_user()
  session.clear()
  return redirect('/')

import views.users
import views.collections
import views.settings
import views.system_setup
import views.rate_setup
import views.reports
import views.data_reset
