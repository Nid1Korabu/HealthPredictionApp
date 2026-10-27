
import os
import re
import math
import sqlite3
from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-development-key")

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patients.db")
AI_MODEL = "gemini-3.6-flash"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_table():
    connection = get_db_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                dob TEXT NOT NULL,
                email TEXT NOT NULL,
                glucose REAL NOT NULL,
                haemoglobin REAL NOT NULL,
                cholesterol REAL NOT NULL,
                remarks TEXT DEFAULT 'AI analysis pending'
            )
        """)
        connection.commit()
    finally:
        connection.close()


def validate_patient(full_name, dob, email, glucose, haemoglobin, cholesterol):
    if not full_name:
        return "Full name is required."

    try:
        birth_date = datetime.strptime(dob, "%d/%m/%Y").date()
        if birth_date > date.today():
            return "Date of birth cannot be in the future."
    except (ValueError, TypeError):
        return "Enter a valid date of birth in dd/mm/yyyy format."

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return "Enter a valid email address."

    try:
        values = [
            float(glucose),
            float(haemoglobin),
            float(cholesterol)
        ]
        if any(not math.isfinite(value) or value <= 0 for value in values):
            return "All health values must be positive numeric values."
    except (ValueError, TypeError):
        return "All health values must be positive numeric values."

    return None


def find_duplicate_patient(
    full_name, dob, email, glucose, haemoglobin, cholesterol,
    exclude_id=None
):
    connection = get_db_connection()
    try:
        query = """
            SELECT id FROM patients
            WHERE LOWER(TRIM(full_name)) = LOWER(TRIM(?))
              AND dob = ?
              AND LOWER(TRIM(email)) = LOWER(TRIM(?))
              AND glucose = ?
              AND haemoglobin = ?
              AND cholesterol = ?
        """
        params = [
            full_name, dob, email,
            float(glucose), float(haemoglobin), float(cholesterol)
        ]

        if exclude_id is not None:
            query += " AND id != ?"
            params.append(exclude_id)

        query += " LIMIT 1"

        return connection.execute(query, params).fetchone()
    finally:
        connection.close()


def generate_ai_remarks(glucose, haemoglobin, cholesterol):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        app.logger.error("GEMINI_API_KEY is missing from the .env file.")
        return None

    prompt = f"""
Generate brief educational health information for a student project.

Glucose: {glucose}
Haemoglobin: {haemoglobin}
Cholesterol: {cholesterol}

The measurement units, laboratory reference ranges, and patient context
are unknown. Do not diagnose a disease or recommend medication.

Explain that the values cannot be interpreted reliably without units
and clinical context. Encourage checking the laboratory reference ranges
and consulting a qualified healthcare professional.

Write 2 to 4 short sentences in plain English. State that this is
general educational information, not a medical diagnosis.
Do not include personal identifying information.
"""

    try:
        with genai.Client(api_key=api_key) as client:
            response = client.models.generate_content(
                model=AI_MODEL,
                contents=prompt
            )

        remarks = (response.text or "").strip()
        return remarks[:1500] if remarks else None

    except Exception as error:
        app.logger.error("Gemini request failed: %s", error)
        return None


def save_ai_remarks(patient_id, glucose, haemoglobin, cholesterol):
    remarks = generate_ai_remarks(glucose, haemoglobin, cholesterol)

    if not remarks:
        return False

    connection = get_db_connection()
    try:
        connection.execute(
            "UPDATE patients SET remarks = ? WHERE id = ?",
            (remarks, patient_id)
        )
        connection.commit()
        return True
    finally:
        connection.close()


@app.route("/")
def home():
    connection = get_db_connection()
    try:
        patients = connection.execute(
            "SELECT * FROM patients ORDER BY id DESC"
        ).fetchall()
    finally:
        connection.close()

    return render_template("index.html", patients=patients)


@app.route("/add", methods=["POST"])
def add_patient():
    full_name = request.form.get("full_name", "").strip()
    dob = request.form.get("dob", "").strip()
    email = request.form.get("email", "").strip()
    glucose = request.form.get("glucose", "").strip()
    haemoglobin = request.form.get("haemoglobin", "").strip()
    cholesterol = request.form.get("cholesterol", "").strip()

    error = validate_patient(
        full_name, dob, email, glucose, haemoglobin, cholesterol
    )
    if error:
        flash(error, "error")
        return redirect(url_for("home"))

    try:
        duplicate = find_duplicate_patient(
            full_name, dob, email, glucose, haemoglobin, cholesterol
        )
    except (ValueError, TypeError):
        flash("Enter valid numeric health values.", "error")
        return redirect(url_for("home"))

    if duplicate:
        flash(
            f"Duplicate record: these details already exist as patient ID "
            f"{duplicate['id']}. No new record was added.",
            "error"
        )
        return redirect(url_for("home"))

    connection = get_db_connection()
    try:
        connection.execute("""
            INSERT INTO patients
            (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            full_name, dob, email,
            float(glucose), float(haemoglobin), float(cholesterol),
            "AI analysis pending"
        ))
        connection.commit()
    finally:
        connection.close()

    flash(
        "Patient record added successfully. Click Generate AI Remarks when ready.",
        "success"
    )
    return redirect(url_for("home"))


@app.route("/edit/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):
    connection = get_db_connection()
    try:
        patient = connection.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
    finally:
        connection.close()

    if patient is None:
        flash("Patient record not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        dob = request.form.get("dob", "").strip()
        email = request.form.get("email", "").strip()
        glucose = request.form.get("glucose", "").strip()
        haemoglobin = request.form.get("haemoglobin", "").strip()
        cholesterol = request.form.get("cholesterol", "").strip()

        error = validate_patient(
            full_name, dob, email, glucose, haemoglobin, cholesterol
        )
        if error:
            flash(error, "error")
            return redirect(url_for("edit_patient", patient_id=patient_id))

        try:
            duplicate = find_duplicate_patient(
                full_name, dob, email, glucose, haemoglobin, cholesterol,
                exclude_id=patient_id
            )
        except (ValueError, TypeError):
            flash("Enter valid numeric health values.", "error")
            return redirect(url_for("edit_patient", patient_id=patient_id))

        if duplicate:
            flash(
                f"These details match another patient record (ID "
                f"{duplicate['id']}). No changes were saved.",
                "error"
            )
            return redirect(url_for("edit_patient", patient_id=patient_id))

        connection = get_db_connection()
        try:
            connection.execute("""
                UPDATE patients
                SET full_name = ?, dob = ?, email = ?, glucose = ?,
                    haemoglobin = ?, cholesterol = ?, remarks = ?
                WHERE id = ?
            """, (
                full_name, dob, email,
                float(glucose), float(haemoglobin), float(cholesterol),
                "AI analysis pending", patient_id
            ))
            connection.commit()
        finally:
            connection.close()

        flash(
            "Patient record updated successfully. Click Generate AI Remarks when ready.",
            "success"
        )
        return redirect(url_for("home"))

    return render_template("edit.html", patient=patient)


@app.route("/analyze/<int:patient_id>", methods=["POST"])
def analyze_patient(patient_id):
    connection = get_db_connection()
    try:
        patient = connection.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
    finally:
        connection.close()

    if patient is None:
        flash("Patient record not found.", "error")
        return redirect(url_for("home"))

    success = save_ai_remarks(
        patient_id,
        patient["glucose"],
        patient["haemoglobin"],
        patient["cholesterol"]
    )

    if success:
        flash("AI remarks generated successfully.", "success")
    else:
        flash(
            "AI remarks could not be generated. Check the terminal and API configuration.",
            "warning"
        )

    return redirect(url_for("home"))


@app.route("/delete/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    connection = get_db_connection()
    try:
        cursor = connection.execute(
            "DELETE FROM patients WHERE id = ?", (patient_id,)
        )
        connection.commit()
        deleted = cursor.rowcount
    finally:
        connection.close()

    if deleted:
        flash("Patient record deleted successfully.", "success")
    else:
        flash("Patient record not found.", "error")

    return redirect(url_for("home"))


create_table()

if __name__ == "__main__":
    app.run(debug=True)
