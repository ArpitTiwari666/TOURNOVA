from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import sqlite3
import os
import uuid
import qrcode

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
QR_FOLDER = os.path.join(BASE_DIR, "qrcodes")
DB_PATH = os.path.join(BASE_DIR, "database.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS tourists (
            id TEXT PRIMARY KEY,
            name TEXT,
            id_number TEXT,
            trip_details TEXT,
            emergency_name TEXT,
            emergency_phone TEXT,
            destination TEXT,
            duration TEXT,
            estimated_price TEXT,
            guide_name TEXT,
            verified INTEGER
        )
        """)
init_db()

@app.route("/submit-kyc", methods=["POST"])
def submit_kyc():
    name = request.form.get("name")
    id_number = request.form.get("id_number")
    trip_details = request.form.get("trip_details")
    emergency_name = request.form.get("emergency_name")
    emergency_phone = request.form.get("emergency_phone")
    id_file = request.files.get("id_file")

    if not id_file:
        return jsonify({"error": "ID file missing"}), 400

    kyc_id = str(uuid.uuid4())[:8]

    destination = "Northeast India"
    duration = "5 Days"
    estimated_price = "₹18,000"
    guide_name = "Certified Local Guide"
    verified = 1

    id_path = os.path.join(UPLOAD_FOLDER, f"{kyc_id}.jpg")
    id_file.save(id_path)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        INSERT INTO tourists VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            kyc_id,
            name,
            id_number,
            trip_details,
            emergency_name,
            emergency_phone,
            destination,
            duration,
            estimated_price,
            guide_name,
            verified
        ))

    qr_url = f"http://127.0.0.1:5050/verify/{kyc_id}"
    qr_img = qrcode.make(qr_url)
    qr_img.save(os.path.join(QR_FOLDER, f"{kyc_id}.png"))

    return jsonify({
    "status": "success",
    "kyc_id": kyc_id,
    "qr": f"http://127.0.0.1:5050/qrcodes/{kyc_id}.png"
})


@app.route("/verify/<kyc_id>")
def verify(kyc_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tourists WHERE id=?", (kyc_id,))
        row = cur.fetchone()

    if not row:
        return "Invalid QR Code"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tourist Digital ID</title>
        <style>
            body {{
                font-family: Arial;
                background: #eef2f5;
                padding: 30px;
            }}
            .card {{
                max-width: 420px;
                margin: auto;
                background: #ffffff;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            }}
            h2 {{
                text-align: center;
                color: #235c41;
            }}
            p {{
                margin: 8px 0;
                font-size: 15px;
            }}
            .verified {{
                color: green;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Tour Nova – Digital Tourist ID</h2>
            <p><b>Name:</b> {row[1]}</p>
            <p><b>Destination:</b> {row[6]}</p>
            <p><b>Duration:</b> {row[7]}</p>
            <p><b>Estimated Cost:</b> {row[8]}</p>
            <p><b>Guide:</b> {row[9]}</p>
            <p><b>Emergency:</b> {row[4]} ({row[5]})</p>
            <p><b>Status:</b> <span class="verified">Verified</span></p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/qrcodes/<filename>")
def serve_qr(filename):
    return send_from_directory(QR_FOLDER, filename)

if __name__ == "__main__":
    app.run(port=5050, debug=True)
