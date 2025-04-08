from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    message = 'Welcome to the Flask form example!'
    name = None
    if request.method == 'POST':
        name = request.form.get('username')  # Retrieve the submitted name from the form
    return render_template('index2.html', message=message, name=name)

if __name__ == "__main__":
    app.run(debug=True)
