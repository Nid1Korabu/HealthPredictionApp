# Health Prediction App

A Flask-based web application for managing patient health records and generating AI-assisted health remarks using the Gemini API.

## About the Project

The Health Prediction App helps users maintain patient records, validate health information, and generate AI-assisted remarks based on entered health measurements.

The application is built with Python and Flask, uses SQLite for persistent data storage, and integrates Google's Gemini API for AI-generated remarks.

**Note:** AI-generated remarks are for educational and informational purposes only. They are not a medical diagnosis or a substitute for professional medical advice.

## Features

- **Patient Management:** Add, view, edit, and delete patient records.
- **Input Validation:** Validate patient details, email addresses, dates of birth, and health measurements.
- **Database Storage:** Store patient information persistently using SQLite.
- **AI-Generated Remarks:** Generate health-related remarks using the Gemini API.
- **Duplicate Record Checks:** Help prevent duplicate patient entries.
- **Web Interface:** Use a simple interface built with HTML and CSS.

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- Google Gemini API
- `python-dotenv`

## Project Structure

```text
HealthPredictionApp/
├── app.py
├── requirements.txt
├── .gitignore
├── templates/
│   ├── index.html
│   └── edit.html
└── static/
    └── style.css
```

The SQLite database is created and managed locally by the application. Environment variables are used to configure sensitive settings.

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Nid1Korabu/HealthPredictionApp.git
cd HealthPredictionApp
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory and add your own credentials:

```env
GEMINI_API_KEY=your_gemini_api_key
FLASK_SECRET_KEY=your_secret_key
```

Replace the placeholder values with your own keys. Never commit your `.env` file or expose API credentials publicly.

### 5. Run the Application

```bash
python app.py
```

Open the local URL displayed in your terminal, typically:

```text
http://127.0.0.1:5000
```

## How to Use

1. Open the application in your browser.
2. Add a patient record using the available form.
3. View patient records in the main table.
4. Edit patient information when required.
5. Generate AI-assisted health remarks for a patient.
6. Delete a record when needed.

## Security and Privacy

- Keep API keys and secret values in environment variables.
- Do not upload `.env`, the local database, or the virtual environment to GitHub.
- Use fictional patient information for testing and demonstrations.
- Avoid entering real patient information into external AI services without appropriate authorization and privacy safeguards.

## Future Improvements

- Add automated unit and integration tests.
- Improve error handling and user feedback.
- Add authentication and role-based access.
- Enhance accessibility and responsive design.
- Improve AI response handling and reporting.

## Author

**Nida Korabu**

GitHub: [Nid1Korabu](https://github.com/Nid1Korabu)

---
