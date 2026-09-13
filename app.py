from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT XAU SENALES DEIVID VIP - ONLINE", 200

@app.route('/test')
def test():
    return "TEST OK", 200
