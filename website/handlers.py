import tornado
import tornado.web
import tornado.gen
from base import BaseHandler, authenticated_async
import forms
import motor
import helper
from models import *

class HomeHandler(BaseHandler):
    def get(self):
        if self.current_user:
            return self.render("authenticated/index.html")
        else:
            return self.render("index.html")

class RegisterHandler(BaseHandler):
    @tornado.gen.engine
    def check_invite(self, invite_code, callback):
        if self.settings['invite_only']:
            if invite_code:
                #Check database to see if invite code is valid.
                spec = {'code': invite_code}
                invite_doc = yield motor.Op(self.db.invites.find_one, spec)
                if invite_doc:
                    invite = Invite(invite_doc)
                    if invite.redeemed_count < invite.total_count or invite.total_count < 0:
                        #Make sure that there are invites left, -1 = unlimited
                        callback(True)

            callback(False)
        else:
            callback(True)


    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        if self.current_user:
            self.redirect('/')
            return

        invite_code = self.get_argument('invite', None)
        is_valid_invite = yield tornado.gen.Task(self.check_invite, invite_code)

        if is_valid_invite:
            self.render("register.html", form=forms.RegistrationForm())
        else:
            form = forms.SignupForm()
            self.render("invite.html", form=form)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self, *args, **kwargs):
        if self.current_user:
            self.redirect('/')
            return

        invite_code = self.get_argument('invite', None)
        is_valid_invite = yield tornado.gen.Task(self.check_invite, invite_code)

        if not is_valid_invite:
            self.redirect('/register')
            return

        form = forms.RegistrationForm(self)
        if not form.validate():
            self.render("register.html", form=form)
            return

        password_hash = helper.hash_password(form.password.data)

        user = User()
        #form.populate_obj(user)
        user.email = form.email.data
        user.password_hash = password_hash
        user.screen_name = form.screen_name.data
        user.zipcode = form.zipcode.data
        user.gender = form.gender.data
        user.birth_date = datetime(form.birth_date_year.data, form.birth_date_month.data, form.birth_date_day.data)
        user.opt_in = form.subscribe.data
        user.invite_code = invite_code

        result = yield motor.Op(self.db.users.insert, user.to_dict())
        user._id = str(result)

        if invite_code:
            #Update the invite table to reflect the use
            spec = { 'code': invite_code }
            update = { '$inc' : {'redeemed_count': 1} }
            yield motor.Op(self.db.invites.update, spec, update)

        #TODO: Send confirmation email!

        self.login_user(user)
        self.redirect('/')

class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/')
            return
        form = forms.LoginForm()
        return self.render("login.html", form=form)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self, *args, **kwargs):
        form = forms.LoginForm(self)
        if form.validate():
            #Check password
            password_hash = helper.hash_password(form.password.data)
            spec = { 'email': form.email.data, 'password_hash': password_hash }
            user_doc = yield motor.Op(self.db.users.find_one, spec)
            if user_doc:
                #Correct Password! Set cookie and redirect to home page
                user = User(**user_doc)
                self.login_user(user, form.remember.data)
                self.redirect('/')
                return
            else:
                #Somehow need to show the invalid login error.
                form.email.errors.append(True)
                form.password.errors.append(True)
                form.errors['invalid'] = True

        self.render("login.html", form=form)

class LogoutHandler(BaseHandler):
    def get(self):
        self.logout_user()

class SignupHandler(BaseHandler):
    def get(self):
        form = forms.SignupForm()
        self.render("signup.html", form=form)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self, *args, **kwargs):
        form = forms.SignupForm(self)

        if form.validate():
            result = yield motor.Op(self.db.signups.insert, { 'email':form.email.data })
            self.redirect('/')

        self.render("signup.html", form=form)