from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT XAU SENALES DEIVID VIP - ONLINE", 200

@app.route('/test')
def test():
    return "TEST OK - Bot vivo", 200

@app.errorhandler(404)
def anti_404(e):
    return "BOT ONLINE - Ve a / o /test", 200
