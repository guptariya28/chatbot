# app.py
# STEP 2: A small website that shows the demand list.

from flask import Flask, render_template
from excel_reader import load_demands

# Create the website
app = Flask(__name__)

# Read the Excel ONCE, when the app starts
demands = load_demands()


# When someone opens the main page ( http://127.0.0.1:5000/ )
# Flask runs this function.
@app.route("/")
def home():
    # The column names = the keys of the first row
    columns = list(demands[0].keys())

    # Fill the page "index.html" with our data and send it to the browser
    return render_template("index.html", demands=demands, columns=columns)


# Start the website when you run:  python app.py
if __name__ == "__main__":
    app.run(debug=True)
