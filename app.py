from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import pdfplumber

app = Flask(__name__)
app.secret_key = "secret123"

# DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.unauthorized_handler
def unauthorized():
    return redirect("/login")

# USER
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.password == request.form["password"]:
            login_user(user)
            return redirect("/")
    return render_template("login.html")

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        user = User(username=request.form["username"], password=request.form["password"])
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# PDF TEXT
def extract_text(file):
    text=""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text+=page.extract_text() or ""
    return text

# ATS SCORE
def score(resume,jd):
    r=set(resume.lower().split())
    j=set(jd.lower().split())
    match=r & j
    score_val=int(len(match)/len(j)*100) if j else 0
    missing=list(j-r)
    return score_val,missing

# SMART SUGGESTIONS (NO API)
def ai_suggestions(resume,jd):
    missing=list(set(jd.lower().split())-set(resume.lower().split()))
    tips="\n".join([f"• Add keyword: {w}" for w in missing[:5]])
    return f"""
Improve Resume:
{tips}

Also:
✔ Add measurable achievements
✔ Use action verbs (Built, Developed)
✔ Add relevant projects
"""

# MAIN
@app.route("/", methods=["GET","POST"])
@login_required
def index():
    result=None
    ai_text=None

    if request.method=="POST":
        file=request.files["resume"]
        jd=request.form["job_desc"]

        resume_text=extract_text(file)
        score_val,missing=score(resume_text,jd)

        ai_text=ai_suggestions(resume_text,jd)

        result={
            "score":score_val,
            "keywords":missing[:10]
        }

    return render_template("dashboard.html",result=result,ai_text=ai_text)

# CHATBOT
@app.route("/chat", methods=["POST"])
def chat():
    msg=request.json["message"]
    return {"reply": f"Tip: Improve '{msg}' using metrics & strong verbs."}

# RUN
if __name__=="__main__":
    app.run(debug=True)