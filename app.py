from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
from flask_sqlalchemy import SQLAlchemy
from sklearn.linear_model import LinearRegression
from flask import send_file
from functools import wraps
import numpy as np
import pickle
import pandas as pd
from flask import session
import os
import google.generativeai as genai
import re
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
load_dotenv()

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "smartfinanceai_secret_key")

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'

db = SQLAlchemy(app)

@app.context_processor
def inject_current_user():
    return dict(
        user_name=session.get("user_name") or "User"
    )


# ==========================
# Login Required Decorator
# ==========================
def login_required(f):
    """
    Ensures a route can only be accessed by a logged-in user.
    Redirects to the login page otherwise.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ==========================
# User Table
# ==========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


# ==========================
# Expense Table
# ==========================
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50))
    amount = db.Column(db.Float)
    date = db.Column(db.String(20))


# ==========================
# Income Table
# ==========================
class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source = db.Column(db.String(100))
    amount = db.Column(db.Float)
    date = db.Column(db.String(20))


# ==========================
# Budget Table
# ==========================
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50))
    budget_amount = db.Column(db.Float)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_name = db.Column(db.String(100))
    target_amount = db.Column(db.Float)

# ==========================
# Home Route
# ==========================
@app.route("/")
def home():
    return redirect(url_for("login"))

# ==========================
# Login Route
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("dashboard"))

        else:
            return "Invalid Email or Password"

    return render_template("login.html")
@app.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]
    user_name = session["user_name"]

    # Notification Count
    notification_count = Notification.query.filter_by(
        is_read=False
    ).count()

    # Latest Notifications
    notification_list = Notification.query.order_by(
        Notification.created_at.desc()
    ).limit(5).all()

    # Settings Notification Switch
    notifications = session.get(
        "notifications",
        True
    )

    # Income
    total_income = sum(
        income.amount
        for income in Income.query.filter_by(user_id=user_id).all()
    )

    # Expense
    total_expense = sum(
        expense.amount
        for expense in Expense.query.filter_by(user_id=user_id).all()
    )

    savings = total_income - total_expense

    total_budgets = Budget.query.filter_by(user_id=user_id).count()

    alert = "No Alerts"

    # Food Budget
    food_budget = Budget.query.filter_by(
        category="Food",
        user_id=user_id
    ).first()

    food_expense = sum(
        expense.amount
        for expense in Expense.query.filter_by(
            category="Food",
            user_id=user_id
        ).all()
    )

    if food_budget and food_expense > food_budget.budget_amount:
        alert = "⚠ Food Budget Exceeded!"

    # Financial Score
    if savings >= 20000:
        score = 95
        status = "Excellent"

    elif savings >= 10000:
        score = 80
        status = "Good"

    elif savings >= 5000:
        score = 65
        status = "Average"

    else:
        score = 40
        status = "Poor"

    # Expense Category Totals
    food_total = sum(
        e.amount
        for e in Expense.query.filter_by(category="Food", user_id=user_id).all()
    )

    travel_total = sum(
        e.amount
        for e in Expense.query.filter_by(category="Travel", user_id=user_id).all()
    )

    bills_total = sum(
        e.amount
        for e in Expense.query.filter_by(category="Bills", user_id=user_id).all()
    )

    shopping_total = sum(
        e.amount
        for e in Expense.query.filter_by(category="Shopping", user_id=user_id).all()
    )

    food_budget_amount = (
        food_budget.budget_amount
        if food_budget else 0
    )

    travel_budget = Budget.query.filter_by(
        category="Travel",
        user_id=user_id
    ).first()

    travel_budget_amount = (
        travel_budget.budget_amount
        if travel_budget else 0
    )

    # Goal
    goal = Goal.query.filter_by(user_id=user_id).first()

    goal_name = "No Goal"
    goal_target = 0
    goal_progress = 0

    if goal:
        goal_name = goal.goal_name
        goal_target = goal.target_amount

        if goal_target > 0:
            goal_progress = round(
                (max(savings, 0) / goal_target) * 100,
                2
            )

    # Recommendation
    recommendation = "Your spending is under control."

    suggestion = "Keep tracking your finances regularly."

    if savings < 0:
        suggestion = "Your expenses exceed your income."

    elif savings < 5000:
        suggestion = "Try saving at least ₹5000 every month."

    else:
        suggestion = "Excellent savings! Consider investing."

    if (
        food_total > food_budget_amount
        and food_budget_amount > 0
    ):
        recommendation = (
            f"Reduce Food Spending by ₹{food_total-food_budget_amount}"
        )

    return render_template(

        "dashboard.html",

        total_income=total_income,

        total_expense=total_expense,

        savings=savings,

        score=score,

        status=status,

        total_budgets=total_budgets,

        alert=alert,

        food_total=food_total,

        travel_total=travel_total,

        bills_total=bills_total,

        shopping_total=shopping_total,

        food_budget_amount=food_budget_amount,

        travel_budget_amount=travel_budget_amount,

        recommendation=recommendation,

        goal_name=goal_name,

        goal_target=goal_target,

        goal_progress=goal_progress,

        suggestion=suggestion,

        user_name=user_name,

        notifications=notifications,

        notification_count=notification_count,

        notification_list=notification_list

    )
# ==========================
# Register Route
# ==========================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("An account with this email already exists. Please log in instead.", "danger")
            return redirect(url_for("register"))

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

# ==========================
# User Settings Table
# ==========================
class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    dark_theme = db.Column(db.Boolean, default=True)
    animations = db.Column(db.Boolean, default=True)
    compact_mode = db.Column(db.Boolean, default=False)
    budget_alerts = db.Column(db.Boolean, default=True)
    goal_alerts = db.Column(db.Boolean, default=True)
    monthly_reports = db.Column(db.Boolean, default=True)
    ai_suggestions = db.Column(db.Boolean, default=True)


# ==========================
# Expense Route
# ==========================
@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():

    user_id = session["user_id"]

    if request.method == "POST":

        category = request.form["category"]
        amount = request.form["amount"]
        date = request.form["date"]

        new_expense = Expense(
            category=category,
            amount=amount,
            date=date,
            user_id=user_id
        )

        db.session.add(new_expense)
        notification = Notification(
            title="Expense Added",
            message=f"₹{amount} added under {category}.",
            icon="wallet"
        )
        
        db.session.add(notification)
        
        db.session.commit()
        
        return redirect("/expense")
    search = request.args.get("search")
    
    if search:
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.category.contains(search)
        ).all()

    else:
        expenses = Expense.query.filter_by(user_id=user_id).all()

    total_expense = sum(
        expense.amount
        for expense in expenses
    )

    return render_template(
        "expense.html",
        expenses=expenses,
        total_expense=total_expense
    )


# ==========================
# Income Route
# ==========================
@app.route("/income", methods=["GET", "POST"])
@login_required
def income():

    user_id = session["user_id"]

    if request.method == "POST":

        source = request.form["source"]
        amount = request.form["amount"]
        date = request.form["date"]

        new_income = Income(
            source=source,
            amount=amount,
            date=date,
            user_id=user_id
        )
        
        db.session.add(new_income)
        
        notification = Notification(
            title="Income Added",
            message=f"₹{amount} received from {source}.",
            icon="cash"
            )
        
        db.session.add(notification)
        
        db.session.commit()

        return redirect("/income")

    incomes = Income.query.filter_by(user_id=user_id).all()

    total_income = sum(
        income.amount
        for income in incomes
    )

    return render_template(
        "income.html",
        incomes=incomes,
        total_income=total_income
    )


# ==========================
# Budget Planner Route
# ==========================
@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():

    user_id = session["user_id"]

    if request.method == "POST":

        category = request.form["category"]
        budget_amount = request.form["budget_amount"]

        new_budget = Budget(
            category=category,
            budget_amount=budget_amount,
            user_id=user_id
        )

        db.session.add(new_budget)
        notification = Notification(
            title="Budget Created",
            message=f"{category} budget created successfully.",
            icon="bar-chart"
            )
        db.session.add(notification)
        
        db.session.commit()
        
        return redirect("/budget")

    budgets = Budget.query.filter_by(user_id=user_id).all()

    return render_template(
        "budget.html",
        budgets=budgets
    )


# ==========================
# Delete Expense Route
# ==========================
@app.route("/delete/<int:id>")
@login_required
def delete(id):

    expense = Expense.query.filter_by(id=id, user_id=session["user_id"]).first()

    if expense:
        db.session.delete(expense)
        db.session.commit()

    return redirect("/expense")



@app.route("/predict")
@login_required
def predict():

    user_id = session["user_id"]

    expenses = Expense.query.filter_by(user_id=user_id).all()

    if len(expenses) < 5:
        return render_template(
        "prediction.html",
        prediction=None,
        message="Please add at least 5 expense records to generate an AI prediction."
    )

    X = np.array(
        range(1, len(expenses) + 1)
    ).reshape(-1, 1)

    y = np.array(
        [expense.amount for expense in expenses]
    )

    model = LinearRegression()

    model.fit(X, y)

    next_month = np.array(
        [[len(expenses) + 1]]
    )

    prediction = model.predict(next_month)

    if prediction[0] < 0:
        prediction[0] = 0

    return render_template(
        "prediction.html",
        prediction=round(prediction[0], 2)
    )

@app.route("/test_goal")
@login_required
def test_goal():

    goal = Goal(
        goal_name="Buy Laptop",
        target_amount=50000,
        user_id=session["user_id"]
    )

    db.session.add(goal)
    db.session.commit()

    return "Goal Added Successfully"

@app.route("/goal", methods=["GET", "POST"])
@login_required
def goal():

    user_id = session["user_id"]

    if request.method == "POST":

        goal_name = request.form["goal_name"]
        target_amount = request.form["target_amount"]

        new_goal = Goal(
            goal_name=goal_name,
            target_amount=target_amount,
            user_id=user_id
        )

        db.session.add(new_goal)
        notification = Notification(
            title="Goal Created",
            message=f"Goal '{goal_name}' added.",
            icon="bullseye"
            )
        
        db.session.add(notification)
        
        db.session.commit()
        
        return redirect("/goal")

    goals = Goal.query.filter_by(user_id=user_id).all()

    return render_template(
        "goal.html",
        goals=goals
    )

# ==========================
# Notification Table
# ==========================

class Notification(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100))

    message = db.Column(db.String(300))

    icon = db.Column(db.String(50))

    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=db.func.now())


@app.route("/financial_health")
@login_required
def financial_health():

    import pandas as pd

    df = pd.read_csv("data/finance_dataset.csv")

    avg_income = round(
        df["monthly_income_usd"].mean(),
        2
    )

    avg_expense = round(
        df["monthly_expenses_usd"].mean(),
        2
    )

    health_score = round(
        ((avg_income - avg_expense) / avg_income) * 100,
        2
    )

    if health_score >= 50:
        status = "Excellent"

    elif health_score >= 30:
        status = "Good"

    else:
        status = "Needs Improvement"

    return render_template(
        "financial_health.html",
        avg_income=avg_income,
        avg_expense=avg_expense,
        health_score=health_score,
        status=status
    )

@app.route("/loan", methods=["GET", "POST"])
@login_required
def loan():

    if request.method == "POST":

        income = float(
            request.form["income"]
        )

        credit_score = float(
            request.form["credit_score"]
        )

        model = pickle.load(
            open("saved_models/loan_model.pkl", "rb")
        )

        prediction = model.predict(
            [[income, credit_score]]
        )

        if prediction[0] == 1:
            result = "Loan Approved ✅"

        else:
            result = "Loan Rejected ❌"

        return render_template(
            "loan_result.html",
            result=result
        )

    return render_template(
        "loan.html"
    )

@app.route("/export")
@login_required
def export():

    user_id = session["user_id"]

    expenses = Expense.query.filter_by(user_id=user_id).all()

    data = []

    for expense in expenses:
        data.append({
            "Category": expense.category,
            "Amount": expense.amount,
            "Date": expense.date
        })

    df = pd.DataFrame(data)

    df.to_excel(
        "expenses_report.xlsx",
        index=False
    )

    return send_file(
        "expenses_report.xlsx",
        as_attachment=True
    )

@app.route("/import_data", methods=["GET", "POST"])
@login_required
def import_data():

    user_id = session["user_id"]

    if request.method == "POST":

        file = request.files["file"]

        if file.filename == "":
            flash("Please select a CSV file.", "danger")
            return redirect(url_for("import_data"))

        try:

            try:
                df = pd.read_csv(file, encoding="utf-8")
            except UnicodeDecodeError:
                file.seek(0)
                df = pd.read_csv(file, encoding="latin1")

            # Clean column names
            df.columns = df.columns.str.strip().str.lower()

            # Rename common column names
            df.rename(columns={
                "category": "Category",
                "amount": "Amount",
                "date": "Date",
                "data": "Date"
            }, inplace=True)

            required_columns = {"Category", "Amount", "Date"}

            if not required_columns.issubset(df.columns):
                flash(
                    "Invalid CSV format. Required columns: Category, Amount, Date.",
                    "danger"
                )
                return redirect(url_for("import_data"))

            imported = 0

            for _, row in df.iterrows():

                expense = Expense(
                    category=str(row["Category"]).strip(),
                    amount=float(row["Amount"]),
                    date=str(row["Date"]).strip(),
                    user_id=user_id
                )

                db.session.add(expense)
                imported += 1

            db.session.commit()

            flash(
                f"{imported} expense records imported successfully!",
                "success"
            )

        except Exception as e:

            flash(f"Import failed: {e}", "danger")

        return redirect(url_for("import_data"))

    return render_template("import_data.html")

@app.route("/delete_all_data")
@login_required
def delete_all_data():

    user_id = session["user_id"]

    Expense.query.filter_by(user_id=user_id).delete()
    Income.query.filter_by(user_id=user_id).delete()
    Budget.query.filter_by(user_id=user_id).delete()
    Goal.query.filter_by(user_id=user_id).delete()

    db.session.commit()

    flash(
        "All financial data deleted successfully!",
        "success"
    )

    return redirect(url_for("settings"))
    
@app.route("/export_income")
@login_required
def export_income():

    user_id = session["user_id"]

    incomes = Income.query.filter_by(user_id=user_id).all()

    data = []

    for income in incomes:
        data.append({
            "Source": income.source,
            "Amount": income.amount,
            "Date": income.date
        })

    df = pd.DataFrame(data)

    df.to_excel(
        "income_report.xlsx",
        index=False
    )

    return send_file(
        "income_report.xlsx",
        as_attachment=True
    )

@app.route("/export_budget")
@login_required
def export_budget():

    user_id = session["user_id"]

    budgets = Budget.query.filter_by(user_id=user_id).all()

    data = []

    for budget in budgets:
        data.append({
            "Category": budget.category,
            "Budget": budget.budget_amount
        })

    df = pd.DataFrame(data)

    df.to_excel("budget_report.xlsx", index=False)

    return send_file(
        "budget_report.xlsx",
        as_attachment=True
    )

@app.route("/export_goal")
@login_required
def export_goal():

    user_id = session["user_id"]

    goals = Goal.query.filter_by(user_id=user_id).all()

    data = []

    for goal in goals:
        data.append({
            "Goal": goal.goal_name,
            "Target": goal.target_amount
        })

    df = pd.DataFrame(data)

    df.to_excel("goal_report.xlsx", index=False)

    return send_file(
        "goal_report.xlsx",
        as_attachment=True
    )

@app.route("/delete_goal/<int:id>")
@login_required
def delete_goal(id):

    goal = Goal.query.filter_by(id=id, user_id=session["user_id"]).first()

    if goal:
        db.session.delete(goal)
        db.session.commit()

    return redirect("/goal")

@app.route("/risk", methods=["GET", "POST"])
@login_required
def risk():

    if request.method == "POST":

        income = float(request.form["income"])
        credit_score = float(request.form["credit_score"])
        loan_amount = float(request.form["loan_amount"])
        debt_ratio = float(request.form["debt_ratio"])
        assets = float(request.form["assets"])
        previous_defaults = int(request.form["previous_defaults"])

        model = pickle.load(
            open("saved_models/risk_model.pkl", "rb")
        )

        prediction = model.predict([[
            income,
            credit_score,
            loan_amount,
            debt_ratio,
            assets,
            previous_defaults
        ]])

        # Convert model output into readable text
        if prediction[0] == 0:
            risk = "Low Risk 🟢"
        elif prediction[0] == 1:
            risk = "Medium Risk 🟡"
        else:
            risk = "High Risk 🔴"

        return render_template(
            "risk_result.html",
            risk=risk
        )

    return render_template("risk.html")

@app.route("/forecast", methods=["GET", "POST"])
@login_required
def forecast():

    if request.method == "POST":

        month = int(
            request.form["month"]
        )

        model = pickle.load(
            open("saved_models/expense_model.pkl", "rb")
        )

        input_data = pd.DataFrame({
            "Month_Number": [month]
            })
        prediction = model.predict(input_data)
        return render_template(
            "forecast_result.html",
            expense=round(prediction[0], 2)
        )

    return render_template(
        "forecast.html"
    )

@app.route("/credit", methods=["GET", "POST"])
@login_required
def credit():

    if request.method == "POST":

        age = int(request.form["age"])
        gender = int(request.form["gender"])
        income = float(request.form["income"])
        education = int(request.form["education"])
        marital_status = int(request.form["marital_status"])
        children = int(request.form["children"])
        home_ownership = int(request.form["home_ownership"])

        model = pickle.load(
            open("saved_models/credit_model.pkl", "rb")
        )

        prediction = model.predict([[
            age,
            gender,
            income,
            education,
            marital_status,
            children,
            home_ownership
        ]])

        score_map = {
            0: "Low",
            1: "Medium",
            2: "High"
        }

        result = score_map.get(
            int(prediction[0]),
            "Unknown"
        )

        return render_template(
            "credit_result.html",
            result=result
        )

    return render_template(
        "credit.html"
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

@app.route("/settings", methods=["GET", "POST"])
def settings():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    user_settings = UserSettings.query.filter_by(user_id=user.id).first()

    if not user_settings:
        user_settings = UserSettings(user_id=user.id)
        db.session.add(user_settings)
        db.session.commit()

    if request.method == "POST":

        new_username = request.form.get("settingsUserName", "").strip()
        new_email = request.form.get("settingsEmail", "").strip()
        new_password = request.form.get("settingsPassword", "").strip()

        # --- Validate email ---
        if new_email and not re.match(EMAIL_REGEX, new_email):
            flash("Invalid email.", "danger")
            return redirect(url_for("settings"))

        # --- Validate username uniqueness ---
        if new_username and new_username != user.name:
            existing = User.query.filter_by(name=new_username).first()
            if existing:
                flash("Username already exists.", "danger")
                return redirect(url_for("settings"))

        # --- Validate password length (only if provided) ---
        if new_password and len(new_password) < 6:
            flash("Password too short.", "danger")
            return redirect(url_for("settings"))

        # --- Apply account updates ---
        if new_username:
            user.name = new_username
            session["user_name"] = new_username

        if new_email:
            user.email = new_email

        if new_password:
            user.password = generate_password_hash(new_password)

        # --- Apply appearance & notification toggles ---
        user_settings.dark_theme = "dark_theme" in request.form
        user_settings.animations = "animations" in request.form
        user_settings.compact_mode = "compact_mode" in request.form
        user_settings.budget_alerts = "budget_alerts" in request.form
        user_settings.goal_alerts = "goal_alerts" in request.form
        user_settings.monthly_reports = "monthly_reports" in request.form
        user_settings.ai_suggestions = "ai_suggestions" in request.form

        db.session.commit()

        flash("Settings saved successfully.", "success")
        return redirect(url_for("settings"))

    return render_template(
        "settings.html",
        user_name=session["user_name"],
        user_email=user.email,
        notification_count=session.get("notification_count", 0),
        notification_list=session.get("notification_list", []),
        dark_theme=user_settings.dark_theme,
        animations=user_settings.animations,
        compact_mode=user_settings.compact_mode,
        budget_alerts=user_settings.budget_alerts,
        goal_alerts=user_settings.goal_alerts,
        monthly_reports=user_settings.monthly_reports,
        ai_suggestions=user_settings.ai_suggestions
        )

@app.route("/profile")
def profile():

    if "user_name" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    total_income = sum(i.amount for i in Income.query.filter_by(user_id=user_id).all())

    total_expense = sum(e.amount for e in Expense.query.filter_by(user_id=user_id).all())

    savings = total_income - total_expense

    return render_template(

        "profile.html",

        user_name=session["user_name"],

        total_income=total_income,

        total_expense=total_expense,

        savings=savings

    )

@app.route("/help")
def help():

    if "user_name" not in session:
        return redirect(url_for("login"))

    return render_template("help.html")

@app.route("/test_notifications")
@login_required
def test_notifications():

    notifications = Notification.query.order_by(
        Notification.created_at.desc()
    ).all()

    text = ""

    for n in notifications:
        text += f"{n.title} - {n.message}<br>"

    return text

@app.route("/mark_notifications_read")
@login_required
def mark_notifications_read():

    Notification.query.update(
        {"is_read": True}
    )

    db.session.commit()

    return "", 204
def _ai_get_reply(user_message):

    try:
        prompt = f"""
        You are SmartFinanceAI, an AI Financial Assistant.
        Always answer as a finance expert.
        Help users with:
        - Budget Planning
        - Expense Tracking
        - Saving Money
        - Investments
        - Credit Score
        - Loans
        - Financial Health
        - Tax Saving
        - Emergency Fund
        - Personal Finance

        Rules:
        1. Never say you are Google Gemini.
        2. Never say you are a language model.
        3. Always introduce yourself as SmartFinanceAI when asked who you are.
        4. Give practical financial advice.
        5. Use simple English.
        6. Use bullet points whenever possible.
        7. Keep answers well structured.

        User Question:
        {user_message}
        """

        response = model.generate_content(prompt)
        text = (response.text or "").strip()

        if not text:
            return "I couldn't come up with an answer for that. Could you rephrase your question?"

        return text[:2500]

    except Exception:
        return "SmartFinanceAI is temporarily unavailable. Please try again in a moment."


@app.route("/assistant", methods=["GET"])
def assistant():

    if "user_name" not in session:
        return redirect(url_for("login"))

    user_name = session["user_name"]

    notification_count = Notification.query.filter_by(
        is_read=False
    ).count()

    notification_list = Notification.query.order_by(
        Notification.created_at.desc()
    ).limit(5).all()

    if "chat_history" not in session:
        session["chat_history"] = []

    return render_template(
        "assistant.html",
        user_name=user_name,
        notification_count=notification_count,
        notification_list=notification_list,
        chat_history=session["chat_history"]
    )


@app.route("/assistant/send", methods=["POST"])
def assistant_send():

    if "user_name" not in session:
        return {"error": "Please log in again."}, 401

    user_message = (request.form.get("user_message") or "").strip()

    if not user_message:
        return {"error": "Please type a message."}, 400

    ai_response = _ai_get_reply(user_message)

    chat = session.get("chat_history", [])
    chat.append({"user": user_message, "bot": ai_response})

    if len(chat) > 20:
        chat = chat[-20:]

    session["chat_history"] = chat
    session.modified = True

    return {"reply": ai_response}


@app.route("/assistant/clear", methods=["POST"])
def assistant_clear():

    if "user_name" not in session:
        return {"error": "Please log in again."}, 401

    session["chat_history"] = []
    session.modified = True

    return {"status": "cleared"}

# ==========================
# Reports Route
# ==========================

@app.route("/reports")
def reports():

    if "user_name" not in session:
        return redirect(url_for("login"))

    notification_count = Notification.query.filter_by(
        is_read=False
    ).count()

    notification_list = Notification.query.order_by(
        Notification.created_at.desc()
    ).limit(5).all()

    return render_template(
        "reports.html",
        user_name=session["user_name"],
        notification_count=notification_count,
        notification_list=notification_list
    )

# ==========================
# Create Database
# ==========================
if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)