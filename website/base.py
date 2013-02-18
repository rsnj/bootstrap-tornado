import logging
import tornado.httpclient
import tornado.web
import tornado.auth
import tornado.escape
from tornado.gen import engine, Task
import functools
import urllib
import urlparse
import helper
import os
import calendar
from datetime import datetime
import bson.objectid

USER_COOKIE_NAME = "user"

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        if not hasattr(self, '_db'):
            self._db = self.settings['db']
        return self._db

    def _handle_error(self, error):
        if error:
            logging.error(error)
            raise tornado.web.HTTPError(500, log_message=error)

    def write_error(self, status_code, **kwargs):
        def get_snippet(fp, target_line, num_lines):
            if fp.endswith('.html'):
                fp = os.path.join(self.get_template_path(), fp)

            half_lines = (num_lines / 2)
            try:
                with open(fp) as f:
                    all_lines = [line for line in f]

                    return ''.join(all_lines[target_line - half_lines:target_line + half_lines])
            except Exception, ex:
                logging.error(ex)

                return ''

        if self.application.settings.get('debug', False) is False:
            if status_code == 404:
                return self.render('errors/404.html')
            elif status_code == 401:
                return self.render('errors/401.html')
            else:
                return self.render('errors/500.html')
        else:
            exception = kwargs.get('exception')
            return self.render('errors/debug.html', get_snippet=get_snippet, exception=exception,
                                      status_code=status_code, kwargs=kwargs)


    def write(self, chunk):
        if isinstance(chunk, dict):
            #The JSON Serializer does not like Python dates so we must encode them properly.
            super(BaseHandler, self).write(helper.to_json(chunk))
        else:
            super(BaseHandler, self).write(chunk)

    def get(self):
        raise tornado.web.HTTPError(404)

    """Lightweight authentication. Only store necessary information in cookie to validate user."""
    def get_current_user(self):
        user_json = self.get_secure_cookie(USER_COOKIE_NAME)
        if user_json:
            user_dict = helper.from_json(user_json)
            user = CookieUser(**user_dict)
            if user and user._id:
                return user

        return None

        """This is the Facbook login logic
        cookies = dict((n, self.cookies[n].value) for n in self.cookies.keys())
        cookie = facebook.get_user_from_cookie(cookies, str(self.settings["facebook"]["api_key"]), self.settings["facebook"]["secret"])

        if not cookie:
            if user_json:
                #We have an old cookie, let's delete it
                self.clear_cookie("user")

            return None

        profile = None
        if user_json:
            profile = tornado.escape.json_decode(user_json)

        if profile and profile["id"] == cookie["uid"]:
            profile["access_token"] = cookie["access_token"]
            return profile

        try:
            # TODO: Make this fetch async rather than blocking
            graph = facebook.GraphAPI(cookie["access_token"])
            profile = graph.get_object("me")

            #Take out unnecessary info
            if "bio" in profile:
                profile.pop("bio")
            if "work" in profile:
                profile.pop("work")
            if "education" in profile:
                profile.pop("education")
            if "quotes" in profile:
                profile.pop("quotes")

        except facebook.GraphAPIError as error:
            return None

        profile["access_token"] = cookie["access_token"]

        self.set_secure_cookie("user", tornado.escape.json_encode(profile), None)

        return profile"""
    def login_user(self, user, remember=False):
        user_dict = user.to_dict()
        cookie_user = CookieUser(**user_dict)

        expires = None
        if remember:
            expires = 90

        self.set_secure_cookie(USER_COOKIE_NAME, helper.to_json(cookie_user.to_dict()), expires_days=expires)

    def logout_user(self):
        self.clear_cookie(USER_COOKIE_NAME)
        self.redirect('/')

    def get_current_user_async(self, callback):
        user = self.get_secure_cookie('user')
        callback(user)

def authenticated_async(method):
    """Decorate methods with this to require that the user be logged in."""
    @functools.wraps(method)
    @engine
    def wrapper(self, *args, **kwargs):
        self._auto_finish = False
        if not hasattr(self, "_current_user"):
            #load the user asynchronously
            self._current_user = yield Task(self.get_current_user_async)

        if not self.current_user:
            if self.request.method in ("GET", "HEAD"):
                url = self.get_login_url()
                if "?" not in url:
                    if urlparse.urlsplit(url).scheme:
                        # if login url is absolute, make next absolute too
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                    url += "?" + urllib.urlencode(dict(next=next_url))
                self.redirect(url)
                return
            raise tornado.web.HTTPError(403)
        else:
            method(self, *args, **kwargs)
    return wrapper

from pymongo.son_manipulator import SONManipulator
class Transform(SONManipulator):
    def transform_incoming(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, Custom):
                son[key] = encode_custom(value)
            elif isinstance(value, dict): # Make sure we recurse into sub-docs
                son[key] = self.transform_incoming(value, collection)
        return son

    def transform_outgoing(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, dict):
                if "_type" in value and value["_type"] == "custom":
                    son[key] = decode_custom(value)
                else: # Again, make sure to recurse into sub-docs
                    son[key] = self.transform_outgoing(value, collection)
        return son

class ContentHandler(BaseHandler):
    def initialize(self, path='content'):
        self.root = os.path.abspath(path) + os.path.sep

    def parse_url_path(self, url_path):
        """Converts a static URL path into a filesystem path.

        ``url_path`` is the path component of the URL with
        ``static_url_prefix`` removed.  The return value should be
        filesystem path relative to ``static_path``.
        """
        if os.path.sep != "/":
            url_path = url_path.replace("/", os.path.sep)
        return url_path

    def get(self, path):
        self.render('content/' + path + '.html')
        #TODO: Check if file exists
        return

        """path = self.parse_url_path(path)
        abspath = os.path.abspath(os.path.join(self.root, path))

        if not os.path.exists(abspath):
            raise tornado.web.HTTPError(404)
        if not os.path.isfile(abspath):
            raise tornado.web.HTTPError(403, "%s is not a file", path)

        self.render(abspath)"""

def timestamp_to_datetime(ts):
    return datetime.utcfromtimestamp(float(ts))


def datetime_to_timestamp(dt):
    return calendar.timegm(dt.timetuple())

class Model(object):
    def __init__(self, *args, **kwargs):
        for key, value in kwargs.iteritems():
            if hasattr(self, key)and  type(value) != dict and type(value) != list:
                if type(value) == bson.objectid.ObjectId:
                    value = str(value)
                setattr(self, key, value)

    def to_dict(self):
        dict = {}
        for attr, value in self.__dict__.iteritems():
            if type(value) != dict and type(value) != list:
                dict[attr] = value

        return dict

    @classmethod
    def object_from_dictionary(cls, entry):
        # make dict keys all strings
        entry_str_dict = dict([(str(key), value) for key, value in entry.items()])
        return cls(**entry_str_dict)

    """def __repr__(self):
        return unicode(self).encode('utf8')"""

class CookieUser(Model):
    _id = None
    screen_name = None
    facebook_id = None
    twitter_id = None