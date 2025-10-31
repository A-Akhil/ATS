# ATS Resume Checker

A Django web application that helps users create ATS-friendly resumes and match them against job descriptions using AI-powered analysis.

## Features

- User registration and authentication
- Profile management with education, skills, and experience
- AI-powered LaTeX resume generation using Gemini API
- BERT-based semantic matching between resumes and job descriptions
- Detailed ATS score breakdowns (education, skills, experience)
- AI-powered improvement suggestions
- Admin panel for user management and scoring configuration
- Modern, responsive UI with Tailwind CSS

## Tech Stack

- **Backend**: Django 5.0
- **Database**: SQLite
- **AI/NLP**:
  - Google Gemini API (resume generation & validation)
  - Sentence-BERT (semantic matching)
  - spaCy (text parsing)
- **Frontend**: Tailwind CSS, Alpine.js
- **LaTeX**: External service at localhost:8006

## Installation

### Prerequisites

- Python 3.9+
- LaTeX compilation service running on localhost:8006
- Gemini API key

### Setup Steps

1. **Clone or navigate to the project**:
```bash
cd /home/akhil/Downloads/temp/ats-check
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Download spaCy model**:
```bash
python -m spacy download en_core_web_sm
```

5. **Create environment file**:
```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your-api-key-here
```

6. **Run migrations**:
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Create superuser** (admin account):
```bash
python manage.py createsuperuser
```
Follow prompts and set role to 'admin' in Django admin after creation.

8. **Run the development server**:
```bash
python manage.py runserver
```

9. **Access the application**:
- Main app: http://localhost:8000
- Django admin: http://localhost:8000/admin

## LaTeX Service

The application requires a LaTeX compilation service running on `localhost:8006`. 

### Start the LaTeX service:

```bash
cd latex-to-pdf
docker build -t latex-service .
docker run -p 8006:8006 latex-service
```

Or use the provided Docker setup in the `latex-to-pdf/` directory.

## Usage

### For Users

1. **Register**: Create an account at `/auth/register/`
2. **Complete Profile**: Fill in education, skills, and experience
3. **Generate Resume**: Use AI to create an ATS-friendly LaTeX resume
4. **Match Jobs**: Paste job descriptions and get ATS match scores
5. **Improve**: Follow AI suggestions to optimize your resume

### For Admins

1. **Access Admin Panel**: Navigate to `/admin/panel/`
2. **Manage Users**: View all registered users
3. **View Match Logs**: See all match attempts and scores
4. **Configure Scoring**: Adjust weights for education (35%), skills (45%), experience (20%)
5. **Set Thresholds**: Configure profession similarity gates

## Project Structure

```
ats-check/
├── ats_checker/          # Django project settings
│   ├── settings.py
│   └── urls.py
├── core/                 # Main application
│   ├── models.py         # Data models
│   ├── views.py          # View controllers
│   ├── forms.py          # Django forms
│   ├── urls.py           # URL routing
│   ├── admin.py          # Django admin config
│   ├── services/         # Business logic
│   │   ├── gemini_service.py    # Gemini API integration
│   │   ├── nlp_service.py       # BERT scoring
│   │   ├── latex_service.py     # LaTeX compilation
│   │   └── scoring_service.py   # Match scoring logic
│   └── templates/        # HTML templates
├── media/                # User uploads
├── requirements.txt      # Python dependencies
├── template.tex          # LaTeX resume template
└── README.md
```

## API Keys and Security

### Gemini API Key

Get your API key from: https://aistudio.google.com/app/apikey

### Security Notes

- **Never commit `.env` file** to version control
- The `STORE_PLAIN_PASSWORD` setting is for development only
- In production, use proper password hashing (Django default)
- Restrict admin panel access to authorized users only

## Database Models

- **User**: Extended Django user with role field
- **Profile**: User profile with education, skills, experience
- **Resume**: Generated or uploaded resumes with LaTeX source
- **JobDescription**: Job descriptions with parsed sections
- **MatchAttempt**: Match results with BERT and Gemini scores
- **AdminSettings**: Singleton for scoring configuration
- **SystemLog**: Audit trail for all user actions

## Scoring Logic

### BERT Scoring
1. **Education Match**: Semantic similarity + degree level comparison
2. **Skills Match**: Exact + semantic matching with breakdown
3. **Experience Match**: Years of experience + semantic comparison

### Profession Gating
- If profession similarity < 0.2: Score = 0 (mismatch)
- If profession similarity < 0.4: Score capped at 30 (transferable skills)
- Otherwise: Full scoring applied

### Final Score
```
Final = (0.35 × Education + 0.45 × Skills + 0.20 × Experience) × 100
```
(Weights are admin-configurable)

### Gemini Validation
- Reviews BERT scores
- Provides corrections if needed
- Generates improvement suggestions

## Development

### Run migrations after model changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create sample data:
Use Django admin or shell to create test users and data.

### Testing:
```bash
python manage.py test
```

## Troubleshooting

### LaTeX Service Not Available
- Ensure Docker service is running: `docker ps`
- Check port 8006 is not in use: `sudo lsof -i :8006`
- Restart the service

### Gemini API Errors
- Verify API key in `.env`
- Check API quota and limits
- Review error messages in console

### BERT Model Issues
- First run downloads the model (may take time)
- Ensure sufficient disk space (~500MB)
- Check internet connection

### Database Issues
- Delete `db.sqlite3` and re-run migrations for fresh start
- Backup database before major changes

## Contributing

This is an academic project. For modifications:
1. Follow Django best practices
2. Update models carefully (requires migrations)
3. Test all features before deployment
4. Document changes in code comments

## License

Academic project - not for commercial use.

## Credits

- **AI Models**: Google Gemini, Sentence-BERT
- **Framework**: Django
- **UI**: Tailwind CSS, Alpine.js
- **Icons**: Font Awesome

## Contact

For issues or questions, refer to project documentation in `work.md`.
