from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT DEIVID OK"

# si este deploy pasa, luego le metemos el bot
