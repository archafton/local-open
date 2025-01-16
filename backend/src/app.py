from flask import Flask, jsonify
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({"message": "Welcome to the Tacitus API"})

if __name__ == '__main__':
    app.run(debug=True)
