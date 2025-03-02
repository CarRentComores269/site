# CarRent Comores Web Application

## Overview
CarRent Comores is a responsive website for car rentals and sales in the Comoros Islands.

## Pages
- Home (`index.html`)
- Rentals (`rentals.html`)
- Sales (`sales.html`)
- About Us (`about.html`)
- Contact (`contact.html`)

## Technologies Used
- HTML5
- CSS3
- Bootstrap 5
- JavaScript

## Project Setup

### Virtual Environment Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize Database Migrations:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. Run the Application:
```bash
flask run
```

### Deactivate Virtual Environment
When you're done working on the project:
```bash
deactivate
```

## Environment Variables
Create a `.env` file with the following variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Flask secret key
- `DEBUG`: Set to True/False

## Dependencies
- Python 3.10+
- Flask
- SQLAlchemy
- PostgreSQL

## Deployment
Configured for Render.com deployment with PostgreSQL database.

## Troubleshooting
- Ensure all dependencies are installed
- Check database connection string
- Verify Python version compatibility

## Getting Started
1. Clone the repository
2. Open `index.html` in a web browser

## Database Migration

### Initial Setup
1. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Initialize Database
```bash
# This will create vehicles.db in your project directory
python app.py
```

### Database Features
- SQLite backend
- Preserves existing localStorage structure
- Seamless migration from browser storage
- Persistent vehicle data across sessions

### Key Endpoints
- `/get_vehicles`: Retrieve all vehicles
- `/add_vehicle`: Add a new vehicle
- `/update_vehicle`: Modify existing vehicle
- `/delete_vehicle`: Remove a specific vehicle
- `/clear_vehicles`: Delete all vehicles

## Compatibility
- Maintains exact localStorage method signatures
- Transparent backend replacement
- No changes required in existing frontend code

## Customization
- Update content in each HTML file
- Modify styles in `css/styles.css`
- Enhance interactivity in `js/main.js`

## Note
Placeholder images are used. Replace them with your actual car and team images.

## Contact
Email: agence@carrentcomores.site
Phone: +269 342 45 43
# site
# site
# site
# site
# site
# site
# site
# site
# site
# site
# site
# site
# site
# site
# site
# site
# site
# site
