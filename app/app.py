from flask import Flask, render_template, request, jsonify
import mysql.connector
import os
import time

app = Flask(__name__)

# Read password from Docker secret file
def get_db_password():
    with open(os.environ.get("DB_PASSWORD_FILE"), "r") as f:
        return f.read().strip()

# MySQL connection with retry
db = None
for i in range(10):
    try:
        db = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=get_db_password(),
            database=os.environ.get("DB_NAME")
        )
        print("Connected to MySQL ✅")
        break
    except Exception as e:
        print("Waiting for MySQL...", e)
        time.sleep(3)

if db is None:
    raise Exception("Database connection failed ❌")

cursor = db.cursor()

# ✅ ADD THIS BLOCK HERE (IMPORTANT)
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT
)
""")
db.commit()

# Home route
@app.route('/')
def index():
    cursor.execute("SELECT message FROM messages ORDER BY id DESC")
    messages = cursor.fetchall()
    return render_template("index.html", messages=messages)

# Submit route
@app.route('/submit', methods=['POST'])
def submit():
    message = request.form.get('new_message')

    if message:
        cursor.execute(
            "INSERT INTO messages (message) VALUES (%s)",
            (message,)
        )
        db.commit()

        return jsonify({"message": message})

    return jsonify({"error": "No input received"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)