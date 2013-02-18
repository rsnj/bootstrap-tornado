import wtforms
from wtforms import validators, StringField, PasswordField, TextAreaField, FileField, HiddenField, FloatField, BooleanField, DateField, widgets
import calendar
from datetime import datetime

BIRTH_DATE_YEAR_MIN = 100
BIRTH_DATE_YEAR_MAX = 17

class TornadoMultiDict(object):
    def __init__(self, handler):
        self.handler = handler
    def __iter__(self):
        return iter(self.handler.request.arguments)
    def __len__(self):
        return len(self.handler.request.arguments)
    def __contains__(self, name):
        # We use request.arguments because get_arguments always returns a
        # value regardless of the existence of the key.
        return name in self.handler.request.arguments
    def getlist(self, name):
        # get_arguments by default strips whitespace from the input data,
        # so we pass strip=False to stop that in case we need to validate
        # on whitespace.
        arguments = self.handler.get_arguments(name, strip=False)
        #if arguments:
        #    for i in range(0, len(arguments)):
        #        arguments[i] = unicode(arguments[i].encode('utf-8'))

        return arguments


class Form(wtforms.Form):
    def __init__(self, handler=None, obj=None, prefix='', formdata=None, **kwargs):
        if handler:
            self.handler = handler
            formdata = TornadoMultiDict(handler)
        wtforms.Form.__init__(self, formdata, obj=obj, prefix=prefix, **kwargs)

class TextInput(widgets.TextInput):
    def __call__(self, field, **kwargs):
        if field.errors:
            c = kwargs.pop('class', '') or kwargs.pop('class_', '')
            kwargs['class'] = u'%s %s' % ('error', c)

        for validator in field.validators:
            if type(validator) == validators.Length and validator.max > 0:
                kwargs['maxlength'] = str(validator.max)

        return super(TextInput, self).__call__(field, **kwargs)

class PasswordInput(widgets.PasswordInput):
    def __call__(self, field, **kwargs):
        if field.errors:
            c = kwargs.pop('class', '') or kwargs.pop('class_', '')
            kwargs['class'] = u'%s %s' % ('error', c)

        for validator in field.validators:
            if type(validator) == validators.Length and validator.max > 0:
                kwargs['maxlength'] = str(validator.max)

        return super(PasswordInput, self).__call__(field, **kwargs)

class Select(widgets.Select):
    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'%s %s' % ('expand', c)

        if field.errors:
            c = kwargs.pop('class', '') or kwargs.pop('class_', '')
            kwargs['class'] = u'%s %s' % ('error', c)

        return super(Select, self).__call__(field, **kwargs)

class SelectField(wtforms.SelectField):
    widget = Select()

def get_months():
    return [(k, v) for k,v in enumerate(calendar.month_name)]

def get_days():
    return [(v,v) for k,v in enumerate(range(1, 32))]

def get_years():
    return [(v,v) for k,v in enumerate(reversed(range(datetime.now().year - BIRTH_DATE_YEAR_MIN, datetime.now().year - BIRTH_DATE_YEAR_MAX)))]

def get_genders():
    return [(1, 'Male'), (2, 'Female')]

class LoginForm(Form):
    email = StringField('Email', [validators.required(), validators.email(), validators.length(max=50)], widget=TextInput())
    password = PasswordField('Password', [validators.required(), validators.length(max=50)], widget=PasswordInput())
    remember = BooleanField('Remember Me')

class RegistrationForm(Form):
    email = StringField('Email', [validators.required(), validators.email(), validators.length(max=50)], widget=TextInput())
    password = PasswordField('Password', [validators.required(), validators.length(max=50)], widget=PasswordInput())
    screen_name = StringField('Screen Name', [validators.required(), validators.length(max=25)], widget=TextInput())
    zipcode = StringField('Zipcode', [validators.required(), validators.length(min=5, max=5)], widget=TextInput())
    birth_date_month = SelectField('Month', [validators.required()], choices=get_months(), coerce=int)
    birth_date_day = SelectField('Day', [validators.required()], choices=get_days(), coerce=int)
    birth_date_year = SelectField('Year', [validators.required()], choices=get_years(), coerce=int)
    gender = SelectField('Gender', [validators.required()], choices=get_genders(), coerce=int)
    subscribe = BooleanField('Subscribe')

class SignupForm(Form):
    email = StringField('Email', [validators.required(), validators.email(), validators.length(max=50)], widget=TextInput())