#!/usr/bin/python3

from flask import redirect, render_template, request
from sqlalchemy.sql import exists, func

import json
import plotly
import plotly.graph_objs as go

from utils import app, db


# Describe database stucture
class Reports(db.Model):

    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    student = db.Column(db.String(4096))
    discipline = db.Column(db.String(4096))
    mark=db.Column(db.Float(asdecimal=False))
    date=db.Column(db.Date)


class Students(db.Model):

    __tablename__='students'

    id = db.Column(db.Integer, primary_key=True)
    student = db.Column(db.String(4096))


class Disciplines(db.Model):

    __tablename__='disciplines'

    id = db.Column(db.Integer, primary_key=True)
    discipline = db.Column(db.String(4096))

db.create_all()


@app.route("/", methods = ['GET', 'POST'])
def index():
    ''' Main page'''

    # Retrieve lists of disciplines from db for <select> menu

    disciplines=db.session.query(Disciplines).all()
    list_disc = [x.discipline for x in disciplines]

    return render_template('index.html', list_disc=list_disc)


@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    """Add student to db"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure student_name was submitted
        if not request.form.get("student_name"):
            return apology("Please provide student's name", 401)

        # Check if student is already in database
        name = request.form.get("student_name")
        q = db.session.query(exists().where(Students.student == name)).scalar()
        if q:
            return apology("The student's name is already in database.", 402)
        else:
            student=Students(student = name)
            db.session.add(student)
            db.session.commit()

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/index.html")
    return redirect('/')


@app.route("/add_disc", methods=["GET", "POST"])
def add_discipline():
    """Add discipline to db"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure discipline was submitted
        if not request.form.get("discipline"):
            return apology("Please provide discipline's name", 401)

        # Check if discipline is already in database
        name = request.form.get("discipline")
        q = db.session.query(exists().where(Disciplines.discipline == name)).scalar()
        if q:
            return apology("The discipline is already in database.", 402)
        else:
            discipline=Disciplines(discipline = name)
            db.session.add(discipline)
            db.session.commit()

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/index.html")
    return redirect('/')


@app.route("/add_mark", methods=["GET", "POST"])
def add_mark():
    """Add mark to db"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure report was submitted
        if not request.form.get("student_name"):
            return apology("Please provide student's name", 401)

        if not request.form.get("discipline"):
            return apology("Please provide discipline's name", 401)

        if not request.form.get("mark"):
            return apology("Please provide a mark", 401)

        if not request.form.get("date"):
            return apology("Please provide a date mark is as for", 401)

        # Check if a student is in db
        name = request.form.get("student_name")
        q = db.session.query(exists().where(Students.student == name)).scalar()
        if not q:
            return apology("The student's name is not in database. Please add it firstly.", 403)

        # Check if a discipline is in a db
        name = request.form.get("discipline")
        q = db.session.query(exists().where(Disciplines.discipline == name)).scalar()
        if not q:
            return apology("The discipline's name is not in database. Please add it firstly.", 403)

        report=Reports(student=request.form.get("student_name"),
                       discipline = request.form.get("discipline"),
                       mark = request.form.get("mark"),
                       date=request.form.get("date")
                       )
        db.session.add(report)
        db.session.commit()

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/index.html")
    return redirect('/')


@app.route("/look_marks", methods=["GET", "POST"])
def look_marks():
    """Get marks and show them for the student for the discipline for the period"""

    # Process the data from input

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure report was submitted
        if not request.form.get("student_name"):
            return apology("Please provide student's name", 401)

        if not request.form.get("discipline"):
            return apology("Please provide discipline's name", 401)

        if not request.form.get("start"):
            return apology("Please provide a start date", 401)

        if not request.form.get("finish"):
            return apology("Please provide a final date", 401)

        # Check if a student is in db
        student = request.form.get("student_name")
        q = db.session.query(exists().where(Students.student == student)).scalar()
        if not q:
            return apology("The student's name is not in database. Please add it firstly.", 403)

        # Check if a discipline is in a db
        discipline = request.form.get("discipline")
        q = db.session.query(exists().where(Disciplines.discipline == discipline)).scalar()
        if not q:
            return apology("The discipline's name is not in database. Please add it firstly.", 403)

        start_date = request.form.get("start")
        final_date = request.form.get("finish")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/index.html")

    # Retrieve data from db
    reports=db.session.query(Reports).filter(Reports.student==student).filter(Reports.discipline==discipline).filter(Reports.date>=start_date).filter(Reports.date<=final_date)

    # Send them to web page
    return render_template('/reports.html', student=student, discipline=discipline, start_date=start_date, final_date=final_date, reports=reports)


@app.route("/graph", methods=["GET", "POST"])
def graph():
    """Get average marks for the period and show them in graph"""

    # Process the data from input

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure report was submitted
        if not request.form.get("start"):
            return apology("Please provide a start date", 401)

        if not request.form.get("finish"):
            return apology("Please provide a final date", 401)

        start_date = request.form.get("start")
        final_date = request.form.get("finish")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/index.html")

    # Retrieve lists of disciplines and dates from db
    dict_disc={}
    disciplines=db.session.query(Disciplines).all()
    reports=db.session.query(Reports).filter(Reports.date>=start_date).filter(Reports.date<=final_date)
    dates=list(map(lambda report: report.date, reports))

    # Retrieve average marks from db
    for discipline in disciplines:
        points_list=[]
        for date in dates:
            date_avg=db.session.query(func.avg(Reports.mark)).filter(Reports.discipline==discipline.discipline).filter(Reports.date==date).scalar()
            if date_avg:
                point=(date, float(date_avg))
                points_list.append(point)
        if points_list:
            points_list.sort(key=lambda x: x[0])
            dict_disc[discipline.discipline]=points_list


    # Make a graph

    # For each discipline create x_scale (dates) and y_scale (average marks)
    data=[]
    for discipline in dict_disc.keys():
        x_scale = list(map(lambda x: x[0], dict_disc[discipline]))
        y_scale = list(map(lambda x: x[1], dict_disc[discipline]))
        trace = go.Scatter(x = x_scale, y = y_scale, name = discipline)
        data.append(trace)

    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    # Make graph
    return render_template('/graph.html', start_date=start_date, final_date=final_date, dict_disc=dict_disc, graphJSON=graphJSON)


def apology(message, code=400):
    """Renders message as an apology to user."""
    return render_template("/apology.html", top=code, bottom=message), code
