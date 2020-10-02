from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = "toto"

from app import routes
