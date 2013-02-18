import os
import tornado.ioloop
import tornado.locale
import tornado.httpserver
import tornado.options
import tornado.web
from tornado.options import define, options
from handlers import *
from base import ContentHandler
import yaml
import motor

"""
Generate new secure cookie
import base64
import uuid

print base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)
"""

define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/register", RegisterHandler),
            (r"/signup", SignupHandler),
            (r"/(.*)", ContentHandler)
        ]

        stream = open('config.yaml', 'r')
        config = yaml.load(stream)

        mongodb_config = config['mongodb']
        connection = motor.MotorClient(mongodb_config['host'], mongodb_config['port']).open_sync()
        config['db'] = connection[mongodb_config['dbname']]

        tornado.web.Application.__init__(self, handlers, **config)

def main():
    tornado.options.parse_command_line()
    tornado.locale.load_translations(os.path.join(os.path.dirname(__file__), "translations"))
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()