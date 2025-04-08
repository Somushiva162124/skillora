from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# In-memory list to store items
items = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

@app.route('/')
def home1():
    return render_template('home1.html', items=items)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        new_item_name = request.form['item_name']
        new_id = max([item['id'] for item in items]) + 1 if items else 1
        items.append({"id": new_id, "name": new_item_name})
        return redirect(url_for('home1'))
    return render_template('add.html')

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit(item_id):
    item = next((item for item in items if item["id"] == item_id), None)
    if not item:
        return "Item not found", 404

    if request.method == 'POST':
        item['name'] = request.form['item_name']
        return redirect(url_for('home1'))

    return render_template('edit.html', item=item)

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete(item_id):
    global items
    items = [item for item in items if item["id"] != item_id]
    return redirect(url_for('home1'))

if __name__ == '__main__':
    app.run(debug=True)
