import os
from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'default_user')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'default_password')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'default_db')

mysql = MySQL(app)


def init_db():
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            title VARCHAR(120) NOT NULL,
            company VARCHAR(120) NOT NULL,
            rate TINYINT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        mysql.connection.commit()
        cur.close()


@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT name, title, company, rate, description, created_at
        FROM reviews
        ORDER BY created_at DESC
    ''')
    rows = cur.fetchall()
    cur.close()

    reviews = [
        {
            'name': r[0],
            'title': r[1],
            'company': r[2],
            'rate': r[3],
            'description': r[4],
            'created_at': r[5].strftime('%Y-%m-%d') if r[5] else '',
        }
        for r in rows
    ]

    avg = round(sum(r['rate'] for r in reviews) / len(reviews), 1) if reviews else 0
    return render_template('index.html', reviews=reviews, avg=avg, total=len(reviews))


@app.route('/submit', methods=['POST'])
def submit():
    name = (request.form.get('name') or '').strip()
    title = (request.form.get('title') or '').strip()
    company = (request.form.get('company') or '').strip()
    description = (request.form.get('description') or '').strip()
    rate_raw = request.form.get('rate')

    if not all([name, title, company, description, rate_raw]):
        return jsonify({'error': 'All fields are required.'}), 400

    try:
        rate = int(rate_raw)
    except ValueError:
        return jsonify({'error': 'Rate must be a number between 1 and 5.'}), 400

    if rate < 1 or rate > 5:
        return jsonify({'error': 'Rate must be between 1 and 5.'}), 400

    cur = mysql.connection.cursor()
    cur.execute(
        'INSERT INTO reviews (name, title, company, rate, description) VALUES (%s, %s, %s, %s, %s)',
        [name, title, company, rate, description],
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({
        'name': name,
        'title': title,
        'company': company,
        'rate': rate,
        'description': description,
    })


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
