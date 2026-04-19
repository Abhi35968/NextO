# NestO (NextO) - Smart Society Management System

NestO is a smart society and apartment management system. It uses FastAPI for the backend and simple HTML/JS for the frontend. The project helps manage daily residential operations like tracking visitors, keeping resident details, collecting maintenance dues, and handling complaints.

---

## Key Features

- **Secure Authentication:** Role-based access control for Admins, Residents, and Security staff.
- **Resident Management:** Keep a central directory of all residents.
- **Visitor Tracking:** Monitor incoming visitors and manage gate entries using QR codes.
- **Maintenance & Billing:** Track society maintenance dues and payment histories.
- **Notice Board:** Send announcements and digital circulars to residents.
- **Complaints & Helpdesk:** A ticketing system for residents to report issues and track their resolution.
- **Dashboard:** An administrative view of society statistics, pending maintenance, and active visitors.

---

## Technology Stack

### Backend
- **Framework:** FastAPI
- **Database:** SQLite with SQLAlchemy ORM
- **Security:** python-jose (JWT) and passlib (bcrypt)
- **Utilities:** qrcode, Pillow, aiofiles
- **Server:** Uvicorn

### Frontend
- HTML5, CSS3, and standard JavaScript
- Responsive dashboard layout

---

## Getting Started

### Prerequisites
You will need Python 3.9 or higher installed on your computer.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/NextO.git
   cd NextO
   ```

2. **Set up a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   source venv/Scripts/activate     # For Windows
   # OR
   source venv/bin/activate         # For Linux / Mac
   ```

3. **Install Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run the Application Server:**
   ```bash
   uvicorn main:app --reload
   ```
   The backend server will run continuously at `http://127.0.0.1:8000`.

---

## API Documentation

Once the server is running, you can access the automatically generated API documentation at these links:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

---

## Project Structure

```text
NextO/
├── backend/
│   ├── main.py              # Application entry point
│   ├── auth.py              # Authentication utilities
│   ├── database.py          # Database setup
│   ├── models.py            # Database tables
│   ├── routers.py           # API endpoints
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Landing / Login page
│   ├── dashboard.html       # Main application dashboard
│   ├── residents.html       # Resident management
│   ├── visitors.html        # Visitor logs
│   ├── maintenance.html     # Maintenance management
│   ├── complaints.html      # Helpdesk module
│   ├── notices.html         # Notice board module
│   └── static/              # CSS, JS, and image assets
└── README.md                # Project documentation
```

---

## Contributing

Contributions are welcome. Feel free to open issues or submit pull requests with improvements.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request
