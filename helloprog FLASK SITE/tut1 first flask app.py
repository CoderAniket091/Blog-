from flask import Flask, render_template

app = Flask(__name__)     #If we create a website then it's an application in flask

@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/name")
def name1():
    name1 = input("Enter your name : \n")
    return f"Hello {name1}"

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/bootstrap")
def bootstrap():
    return render_template('bootstrap.html')

# app.run()
app.run(debug=True) #If you do this then it will return your change instantly and don't need to restart
