import pyodbc
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime as dt
from datetime import date
from datetime import timedelta
from geopy.distance import geodesic

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SecureSecretKey'


def connection():    
    server = 'txt6312server.database.windows.net'
    database = 'test'
    username = 'CloudSA3d95adf8'
    password = 'tiger@123TT'
    driver = '{ODBC Driver 18 for SQL Server}'
    conn = pyodbc.connect(
        'DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    return conn


@app.route('/', methods=['GET', 'POST'])
def main():
    try:
        conn = connection()
        cursor = conn.cursor()
        return render_template('index.html')
    except Exception as e:
        return render_template('index.html', error=e)


#Search by Magnitude


class Form1(FlaskForm):
    mag = StringField(label='Enter Magnitude: ', validators=[DataRequired()])
    submit = SubmitField(label='Submit')


@app.route('/form1', methods=['GET', 'POST'])
def form1():
    form = Form1()
    cnt = 0
    if form.validate_on_submit():
        try:
            conn = connection()
            cursor = conn.cursor()
            mag = float(form.mag.data)
            if mag <= 5.0:
                return render_template('form1.html', form=form, error="Magnitude must be > 5.0", data=0)

            cursor.execute("SELECT * FROM earthquake1 where mag > ?", mag)
            result = []
            while True:
                row = cursor.fetchone()
                if not row:
                    break
                result.append(row)
                cnt += 1
            return render_template('form1.html', result=result, cnt=cnt, mag=mag, form=form, data=1)

        except Exception as e:
            print(e)
            return render_template('form1.html', form=form, error="Magnitude must be numeric.", data=0)

    return render_template('form1.html', form=form)


#Search by Range & Days


class Form2(FlaskForm):
    r1 = StringField(label='Enter Magnitude Range 1: ', validators=[DataRequired()])
    r2 = StringField(label='Enter Magnitude Range 2: ', validators=[DataRequired()])
    days = StringField(label='Enter Days: ', validators=[DataRequired()])
    submit = SubmitField(label='Submit')


@app.route('/form2', methods=['GET', 'POST'])
def form2():
    form = Form2()
    if form.validate_on_submit():
        try:
            conn = connection()
            cursor = conn.cursor()
            r1 = float(form.r1.data)
            r2 = float(form.r2.data)
            days = int(form.days.data)
            cnt = 0

            if days > 30 or r1 > r2:
                raise Exception()
            today = date.today()
            days_ago = today - timedelta(days=days)
            print(days_ago)

            cursor.execute("SELECT * FROM earthquake1 where time > ? AND mag BETWEEN ? AND ?", days_ago, r1, r2)
            result = []
            while True:
                row = cursor.fetchone()
                if not row:
                    break
                result.append(row)
                cnt += 1
            return render_template('form2.html', result=result, cnt=cnt, r1=r1, r2=r2, days=days, form=form, data=1)

        except Exception as e:
            print(e)
            return render_template('form2.html', form=form, error="Range 1 and Range 2 must be numeric, Range 1 > Range 2 and Days must be integer and less then 31.", data=0)

    return render_template('form2.html', form=form, data=0)


#Search by Location


class Form3(FlaskForm):
    lat = StringField(label='Enter Latitude: ', validators=[DataRequired()])
    lon = StringField(label='Enter Longitude: ', validators=[DataRequired()])
    km = StringField(label='Enter Kilometers: ', validators=[DataRequired()])
    submit = SubmitField(label='Submit')


@app.route('/form3', methods=['GET', 'POST'])
def form3():
    form = Form3()
    if form.validate_on_submit():
        try:
            conn = connection()
            cursor = conn.cursor()
            lat = float(form.lat.data)
            lon = float(form.lon.data)
            km = float(form.km.data)
            cnt = 0

            cursor.execute("SELECT time, latitude, longitude, mag, id, place, type FROM earthquake1")
            result = []
            while True:
                row = cursor.fetchone()
                if not row:
                    break
                if geodesic((float(row[1]), float(row[2])), (lat, lon)).km <= km:
                    result.append(row)
                    cnt += 1
            return render_template('form3.html', result=result, cnt=cnt, lat=lat, lon=lon, km=km, form=form, data=1)

        except Exception as e:
            print(e)
            return render_template('form3.html', form=form, error="Latitude must be in the [-90; 90] range, Latitude must be in [-180; 180] and all input must be numaric.")
    return render_template('form3.html', form=form, data=0)


#Search by Clusters


@app.route('/form4', methods=['GET', 'POST'])
def form4():
    if request.method == 'POST':
        try:
            conn = connection()
            cursor = conn.cursor()
            clus = request.form['clus']
            cnt = 0

            cursor.execute("SELECT * FROM earthquake1 where type = ?", clus)
            result = []
            while True:
                row = cursor.fetchone()
                if not row:
                    break
                result.append(row)
                cnt += 1
            return render_template('form4.html', result=result, cnt=cnt, clus=clus, data=1)

        except Exception as e:
            print(e)
            return render_template('form4.html', error="Range 1 and Range 2 must be numeric, Range 1 > Range 2 and Days must be integer and less then 31.", data=0)

    return render_template('form4.html', data=0)


#Does given Magnitude occur more often at night?


@app.route('/form5', methods=['GET', 'POST'])
def form5():
    cnt = 0
    tot_cnt = 0
    try:
        conn = connection()
        cursor = conn.cursor()

        cursor.execute('select * from earthquake1 where mag > 4.0')
        result = []
        while True:
            row = cursor.fetchone()
            if not row:
                break
            hour = dt.strptime(row[0], '%Y-%m-%dT%H:%M:%S.%fZ').hour
            if hour > 18 or hour < 7:
                result.append(row)
                cnt += 1
            tot_cnt += 1
        return render_template('form5.html', result=result, cnt=cnt, tot_cnt=tot_cnt, data=1)

    except Exception as e:
        print(e)
        return render_template('form5.html', error="Magnitude must be numeric.", data=0)


if __name__ == "__main__":
    app.run(debug=True)