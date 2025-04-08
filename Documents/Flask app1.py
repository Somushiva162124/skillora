from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    message = "Welcome to My Flask App1!"
    return render_template('index1.html', message=message)

@app.route('/about')
def about():
    return render_template('index1.html', message="This is the About Page!")

if __name__ == '__main__':
    app.run(debug=True)
