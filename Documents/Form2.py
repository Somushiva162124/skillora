from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# In-memory storage for user registrations (just for this activity)
user_data = []

@app.route('/')
def home():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # Form validation
    if not name or not email or not password or not confirm_password:
        flash("All fields are required!", "error")
        return redirect(url_for('home'))
    
    if password != confirm_password:
        flash("Passwords do not match!", "error")
        return redirect(url_for('home'))

    if '@' not in email or '.' not in email:
        flash("Invalid email format!", "error")
        return redirect(url_for('home'))

    # Store user data (in memory)
    user_data.append({
        'name': name,
        'email': email,
    })

    flash(f"Registration successful! Welcome, {name}!", "success")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
