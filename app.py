from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)

app.config["SECRET_KEY"] = "art126in"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# orm models


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    submissions = db.relationship("Submission", backref="submitter", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}')"


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    submitted_by = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Submission('{self.name}', {self.age})"


with app.app_context():
    db.create_all()

# Decorators


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            flash("You need login to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function

# route


@app.route("/")
def home():
    page_title = "dynamic Glask Page"
    username = session.get("name", None)
    submission = Submission.query.order_by(Submission.id.desc()).all()

    languages_stats = {"Python": len(submission),"JavaScript": 0, "HTML/CSS": 0, "SQL": 0}
    return render_template(
        "index.html", title=page_title, stats=languages_stats, username=username, submission=submission,

    )


@app.route("/about")
def about():
    username = session.get("name", None)
    return render_template("about.html", title="About us", username=username)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("This email is already registered", "error")
            return redirect(url_for("register"))

        new_user = User(name=name, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Plaase Log In", "success")
        return redirect(url_for("login"))

    return render_template("register.html", title="Register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["logged_in"] = True
            session["email"] = user.email
            session["name"] = user.name
            session["user_id"] = user.id
            flash(f"welcome back {user.name}", "success")
            return redirect(url_for("home"))
        else:
            flash("invalid email or passsword", "error")
            return redirect(url_for("login"))
    return render_template("login.html", title="Log in")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("email", None)
    session.pop("name", None)
    session.pop("user_id", None)
    flash("you are now logged out", "info")
    return redirect(url_for("home"))


@app.route("/submit", methods=["GET", "POST"])
@login_required
def submit():
    if request.method == "POST":

        user_name = request.form.get("user_input_name")
        user_age = request.form.get("user_input_age")
        user_id = session.get("user_id")
        submitted_by = session.get("name", "Anonymous")

        if not user_id:
            flash("Authenrication error: Please Log In again", "error")
            return redirect(url_for("login"))

        if user_name and user_age and user_id:
                try:
                    age_int = int(user_age)

                    if age_int <= 0:
                        flash("Age must be a positive number", "error")
                        return redirect(url_for("submit"))
                except ValueError:
                    flash("Age must be a valid number", "error")
                    return redirect(url_for("submit"))


                new_submission = Submission(
                    user_id=user_id,
                    name=user_name,
                    age=age_int,
                    submitted_by=submitted_by
                )
                db.session.add(new_submission)
                db.session.commit()

                flash("Dara Submitted successfully", "success")
                return redirect(url_for("home"))

        else:
            flash("Name and Age are required", "error")
            return redirect(url_for("submit"))

    return render_template("name_form.html", title="Submit Your Name")

@app.route("/delete/<int:submission_id>", methods=["POST"])
@login_required
def delete_submission(submission_id):

    submission = Submission.query.get_or_404(submission_id)

    current_user_id = session.get("user_id")

    if submission.user_id != current_user_id:
        flash("You do not have permission to delete this submission", "error")
        return redirect(url_for("home"))
    
    try:
        db.session.delete(submission)
        db.session.commit()
        flash(f"Submission ID {submission_id} for '{submission.name}' deleted successfully", "success")
    except:
        db.session.rollback()
        flash("An error occurd while deleting the submission", "error")
    
    return redirect(url_for("home"))

if __name__ == "__main__":
    @app.route("/greet/<string:name>/<int:age>")
    @login_required
    def greet(name, age):
        return render_template("greet.html", name=name, age=age)
    app.run(debug=True)
