# Make it run from the examples directory
import sys
sys.path.append("../../liquer")

from liquer import *
import liquer.ext.basic
import liquer.ext.meta
import liquer.ext.lq_pandas
from liquer.context import RecipeSpecStore
from liquer.store import web_mount, mount, FileStore

### Create Flask app and register LiQuer blueprint
from flask import Flask
import liquer.server.blueprint as bp
app = Flask(__name__)

url_prefix='/liquer'
app.register_blueprint(bp.app, url_prefix=url_prefix)

mount("data")

@first_command(volatile=True)
def hello():
    return "Hello"

@app.route('/')
@app.route('/index.html')
def index():
    return open("../index.html").read()


if __name__ == '__main__':
    app.run()
