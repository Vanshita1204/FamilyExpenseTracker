import sqlite3
from datetime import datetime

from flask import current_app as app
from flask import redirect, render_template, request
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from werkzeug.security import check_password_hash, generate_password_hash

from .database import db
from .models import Expense, Member, User

con = sqlite3.connect("user.db")

cur = con.cursor()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/notfound/Unauthorized"


# ==============================Business Logic====================================
# ------------Login-Logout-------------
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# -------------------------


@app.route("/")
def home():
    return render_template("home.html")


# -------------------------
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form.get("name")
        passd = request.form.get("password")
        try:
            user = User.query.filter(User.name == uname).one()
        except:
            return render_template("login.html", error="incorrect username")
        if not check_password_hash(user.password, password=passd):
            return render_template("login.html", error="incorrect password")
        if not current_user.is_active:
            login_user(user)
    if current_user.is_active:
        return dashboard()
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        uname = request.form.get("name")
        passd = request.form.get("password")

        if uname not in (i.name for i in User.query.all()):
            user = User(name=uname, password=generate_password_hash(passd))
            db.session.add(user)
            db.session.commit()
            return login()
        return redirect("/notfound/User already exists.")
    return render_template("signup.html")


# -----------------------------------------
@app.route("/notfound/<error>")
def notfound(error):
    return render_template("notfound.html", error=error)


# -----------------------------------------------------------------------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


# ------------------------------------------------------------------------------------------------------------------------------------


@app.route("/member/add", methods=["GET", "POST"])
def add():

    if request.method == "POST":
        mname = request.form.get("mem_name")
        mage = request.form.get("mem_age")
        mlimit = request.form.get("mem_limit")
        member = Member(
            name=mname,
            age=mage,
            total_expense=0,
            limit=mlimit,
            user_id=current_user.get_id(),
        )
        db.session.add(member)
        db.session.commit()
        return dashboard()
    return render_template("add.html")


@app.route("/member/<int:id>/edit", methods=["GET", "POST"])
@login_required
def update_member(id):
    if (id,) not in db.session.query(Member.id).all():
        return notfound("member_id_not_found")
    t = Member.query.get(id)
    if request.method == "POST":
        try:
            if (
                request.form.get("mem_name") != t.name
                or request.form.get("mem_age") != t.age
            ):
                db.session.query(Expense).filter(Expense.id == id).delete()
            updict = {
                Member.name: request.form["mem_name"],
                Member.age: request.form["mem_age"],
                Member.limit: request.form["mem_limit"],
            }
            print(updict)
            db.session.query(Member).filter(Member.id == id).update(updict)
            db.session.commit()
            return dashboard()
        except:
            print("-------------db_update_error--------------")
            db.session.rollback()

    return render_template("edit.html", member=t, user=current_user)


@app.route("/member/<int:id>/delete", methods=["GET", "POST"])
@login_required
def delete_member(id):
    # Validation
    if (id,) not in db.session.query(Member.id).all():
        print("d")
        return notfound("member_id_not_found")
    t = Member.query.get(id)
    try:
        db.session.delete(t)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("----member_delete_dberror------", e)
    return dashboard()


# ------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/member/<int:id>", methods=["GET", "POST"])
@login_required
def view(id):
    if (id,) not in db.session.query(Member.id).all():
        print("m")
        return notfound("member_id_not_found")
    m = Member.query.get(id)
    me = Expense.query.filter(Expense.member_id == id).order_by(Expense.created_date)
    x, y = [], []
    fig = plt.figure(figsize=(8, 5))
    ax = fig.gca()
    if request.method == "POST" and request.form.get(
        "period"
    ):  # to remove bug from direct function call
        p = request.form.get("period")
        if p == "Custom":
            llim = request.form["customdatetimel"]
            hlim = request.form["customdatetimeh"]
            comp = "%Y-%m-%dT%H:%M"
        elif p == "Today":
            llim = datetime.today().strftime("%d/%m/%y")
            hlim = llim
            comp = "%d/%m/%y"
        elif p == "1Month":
            llim = datetime.today().strftime("%m/%y")
            hlim = llim
            comp = "%m/%y"
        elif p == "All":
            llim, hlim, comp = "", "", ""
    else:
        llim, hlim, comp = "", "", ""

    for i in me:
        if (
            i.created_date.strftime(comp) >= llim
            and i.created_date.strftime(comp) <= hlim
        ):
            x.append(i.created_date)
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            plt.ylabel("Int")
            y.append(int(i.amount))
    plt.plot(x, y, marker="o", color="b", linestyle="--")
    plt.gcf().autofmt_xdate()
    plt.savefig("static/chart.png")
    if len(x) > 0:
        img = "/static/chart.png"
    else:
        img = ""
    return render_template("view.html", member=m, chart=img)


@app.route("/<int:id>/expense/add", methods=["GET", "POST"])
@login_required
def add_expense(id):
    if (id,) not in db.session.query(Member.id).all():
        return notfound("member_id_not_found")
    m = Member.query.get(id)
    if request.method == "POST":
        try:
            amt = request.form.get("amt")
            cat = request.form.get("category")
            m.total_expense = Member.total_expense + amt
            created = datetime.strptime(
                request.form.get("time"), "%d/%b/%Y, %H:%M:%S.%f"
            )
            e = Expense(member_id=id, created_date=created, category=cat, amount=amt)
            db.session.add(e)
            db.session.commit()
            return view(id)

        except e:
            db.session.rollback()
            print("-------------db_log_add_error--------------")
        return render_template("add_expense.html", member=m, datetime=datetime)
    return render_template(
        "add_expense.html", member=Member.query.get(id), datetime=datetime
    )


@app.route("/expense/<int:id>/editex", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    if (id,) not in db.session.query(Expense.id).all():
        return notfound("expense_id_not_found")
    e = Expense.query.get(id)
    mid = e.member_id
    m = Member.query.filter(Member.id == mid).one()
    a = e.amount
    print(a)
    if request.method == "POST":
        try:
            amt = request.form.get("amt")
            cat = request.form.get("category")
            created = datetime.strptime(
                request.form.get("time"), "%d/%b/%Y, %H:%M:%S.%f"
            )
            db.session.delete(e)

            e = Expense(member_id=mid, created_date=created, category=cat, amount=amt)
            m.total_expense = Member.total_expense - a + amt

            db.session.add(e)
            db.session.commit()
            return view(mid)
        except:
            db.session.rollback()
            print("-------------db_log_update_error--------------")
        return render_template("edit_expense.html", member=m, datetime=datetime)
    return render_template("edit_expense.html", member=m, datetime=datetime)


@app.route("/expense/<int:id>/delete", methods=["GET", "POST"])
@login_required
def delete_log(id):
    # validation
    if (id,) not in db.session.query(Expense.id).all():
        return notfound("expense_id_not_found")
    e = Expense.query.get(id)
    mid = e.member_id
    m = Member.query.filter(Member.id == mid).one()

    m.total_expense = Member.total_expense - e.amount

    db.session.delete(e)
    db.session.commit()
    return view(mid)
