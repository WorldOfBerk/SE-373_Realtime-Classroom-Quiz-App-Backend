from flask import Flask
from routes.login import login_bp
from routes.session import session_bp
from routes.quiz import quiz_bp

app = Flask(__name__)
app.register_blueprint(login_bp)
app.register_blueprint(session_bp)
app.register_blueprint(quiz_bp)

@app.route('/')
def home():
    return "Welcome to the Classroom Quiz API", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
