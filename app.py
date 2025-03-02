from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, Response, send_file, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import traceback
import logging
import queue
import threading
import time
from datetime import datetime
from sqlalchemy import text
import shutil
from flask_migrate import Migrate

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),
                        logging.FileHandler('carrent_debug.log')
                    ])

# Create Flask app with explicit template and static folders
app = Flask(__name__, 
            template_folder='.', 
            static_folder='static',  # Explicitly set static folder
            static_url_path='')      # Serve static files from root

app.secret_key = os.environ.get('SECRET_KEY', '265afb09533257ad9db63f7eadc3f798')

# Ensure instance folder exists for database
os.makedirs('instance', exist_ok=True)

# Enhanced Database Configuration Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definitive Database URI Configuration
def get_database_uri():
    # Prioritized list of potential database URIs
    potential_uris = [
        os.environ.get('DATABASE_URL'),
        os.environ.get('DB_CONNECTION_STRING'),
        f"postgresql://{os.environ.get('DB_USERNAME', 'carrent_user')}:"
        f"{os.environ.get('DB_PASSWORD', 'WfBNpgfvZEcSoUTruafyT8wE9MFEYyhs')}@"
        f"{os.environ.get('DB_HOST', 'dpg-cv21qj0gph6c73bbq1lg-a.oregon-postgres.render.com')}/"
        f"{os.environ.get('DB_NAME', 'carrent_ak7c')}?sslmode=require",
        'sqlite:///instance/carrent.db'  # Absolute fallback
    ]

    # Validate and return the first valid URI
    for uri in potential_uris:
        if uri:
            try:
                from sqlalchemy.engine.url import make_url
                make_url(uri)
                print(f"Using database URI: {uri}")
                return uri
            except Exception as e:
                print(f"Invalid URI {uri}: {e}")

    # If no valid URI is found, raise a critical error
    raise ValueError("No valid database URI could be constructed")

# Set the database URI with absolute certainty
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()

# Ensure additional SQLAlchemy configurations
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 10,
    'max_overflow': 20,
    'connect_args': {
        'sslmode': 'require',
        'application_name': 'CarRent Comores App'
    }
}

# Fallback database initialization
def init_db():
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Call initialization during app context
with app.app_context():
    init_db()

# Vehicle Model matching localStorage structure
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    transmission = db.Column(db.String(50), nullable=False)
    passengers = db.Column(db.Integer, nullable=False)
    gasType = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(500))
    status = db.Column(db.String(50), default='Available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Sales Vehicle Model
class SalesVehicle(db.Model):
    __tablename__ = 'sales_vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    color = db.Column(db.String(50), nullable=False)
    engine_size = db.Column(db.String(20), nullable=False)
    gas_type = db.Column(db.String(20), nullable=False)
    drivetrain = db.Column(db.String(20), nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    features = db.Column(db.Text)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    transmission = db.Column(db.String(50), nullable=False)
    mileage = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'make': self.make or '',
            'model': self.model or '',
            'year': self.year or 0,
            'category': self.category or '',
            'condition': self.condition or '',
            'price': self.price or 0.0,
            'color': self.color or '',
            'engineSize': self.engine_size or '',
            'gasType': self.gas_type or '',
            'drivetrain': self.drivetrain or '',
            'plateNumber': self.plate_number or '',
            'features': self.features.split(',') if self.features else [],
            'description': self.description or '',
            'image': f'/uploads/sales_vehicles/{self.image}' if self.image else None,
            'transmission': self.transmission or '',
            'mileage': self.mileage,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

# Booking Model
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    vehicle_plate = db.Column(db.String(50), nullable=False)
    vehicle_name = db.Column(db.String(100), nullable=False)
    vehicle_category = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    rental_days = db.Column(db.Integer, nullable=False)
    base_rate = db.Column(db.Float, nullable=False)
    additional_services = db.Column(db.String(100), nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    status_notes = db.Column(db.Text)
    additional_services_details = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint('customer_name', 'vehicle_name', 'start_date', name='unique_booking'),
    )

# Robust Database Backup Function
def backup_database(db_path='instance/carrent.db'):
    """
    Create a backup of the SQLite database with error handling
    """
    import os
    import shutil
    from datetime import datetime

    try:
        # Ensure instance directory exists
        os.makedirs('instance', exist_ok=True)

        # Create backup directory if it doesn't exist
        backup_dir = 'database_backups'
        os.makedirs(backup_dir, exist_ok=True)

        # If database doesn't exist, create an empty one
        if not os.path.exists(db_path):
            print(f"Database {db_path} does not exist. Creating an empty database.")
            open(db_path, 'a').close()

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{backup_dir}/carrent_backup_{timestamp}.db"

        # Perform backup
        try:
            shutil.copy2(db_path, backup_filename)
            print(f"Database backup created: {backup_filename}")
        except Exception as copy_error:
            print(f"Error creating database backup: {copy_error}")

    except Exception as e:
        print(f"Unexpected error in database backup: {e}")

# Modify to handle PostgreSQL and SQLite
def safe_backup_database():
    """
    Safely attempt database backup based on current configuration
    """
    try:
        # Check if using SQLite
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            backup_database()
        else:
            print("Skipping backup for non-SQLite database")
    except Exception as e:
        print(f"Error in safe database backup: {e}")

# Schedule backup during app initialization
with app.app_context():
    try:
        safe_backup_database()
    except Exception as e:
        print(f"Backup initialization error: {e}")

# Create tables
with app.app_context():
    # Remove db.drop_all() to preserve existing data
    
    # Recreate tables only if they don't exist
    db.create_all()
    
    # Optional: Add a print statement to confirm table creation
    print("Database tables ensured to exist.")
    
    # Automatically create a backup when the application starts
    safe_backup_database()

# Set logging level for Flask app
app.logger.setLevel(logging.DEBUG)

# Real-time Booking Updates
booking_event_queue = queue.Queue()

def generate_booking_events():
    while True:
        event = booking_event_queue.get()
        yield f"data: {json.dumps(event)}\n\n"

@app.route('/booking_updates')
def booking_updates():
    return Response(
        generate_booking_events(), 
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

# Routes to mimic localStorage behavior
@app.route('/get_vehicles', methods=['GET'])
def get_vehicles():
    vehicles = Vehicle.query.order_by(Vehicle.id.desc()).all()
    return jsonify([{
        'plate': v.plate,
        'name': v.name,
        'category': v.category,
        'price': v.price,
        'transmission': v.transmission,
        'passengers': v.passengers,
        'gasType': v.gasType,
        'description': v.description,
        'image': v.image,
        'status': v.status
    } for v in vehicles])

@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    data = request.json
    
    # Check if vehicle with same plate already exists
    existing_vehicle = Vehicle.query.filter_by(plate=data['plate']).first()
    if existing_vehicle:
        return jsonify({'error': 'Vehicle with this plate already exists'}), 400
    
    new_vehicle = Vehicle(
        plate=data['plate'],
        name=data['name'],
        category=data['category'],
        price=data['price'],
        transmission=data['transmission'],
        passengers=data['passengers'],
        gasType=data['gasType'],
        description=data.get('description', ''),
        image=data.get('image', ''),
        status=data.get('status', 'Available')
    )
    
    db.session.add(new_vehicle)
    db.session.commit()
    
    return jsonify({
        'message': 'Vehicle added successfully',
        'vehicle': {
            'plate': new_vehicle.plate,
            'name': new_vehicle.name,
            'category': new_vehicle.category,
            'price': new_vehicle.price,
            'transmission': new_vehicle.transmission,
            'passengers': new_vehicle.passengers,
            'gasType': new_vehicle.gasType,
            'description': new_vehicle.description,
            'image': new_vehicle.image,
            'status': new_vehicle.status
        }
    }), 201

@app.route('/update_vehicle', methods=['POST'])
def update_vehicle():
    data = request.json
    vehicle = Vehicle.query.filter_by(plate=data['plate']).first()
    
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404
    
    # Update vehicle details
    vehicle.name = data.get('name', vehicle.name)
    vehicle.category = data.get('category', vehicle.category)
    vehicle.price = data.get('price', vehicle.price)
    vehicle.transmission = data.get('transmission', vehicle.transmission)
    vehicle.passengers = data.get('passengers', vehicle.passengers)
    vehicle.gasType = data.get('gasType', vehicle.gasType)
    vehicle.description = data.get('description', vehicle.description)
    vehicle.image = data.get('image', vehicle.image)
    vehicle.status = data.get('status', vehicle.status)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Vehicle updated successfully',
        'vehicle': {
            'plate': vehicle.plate,
            'name': vehicle.name,
            'category': vehicle.category,
            'price': vehicle.price,
            'transmission': vehicle.transmission,
            'passengers': vehicle.passengers,
            'gasType': vehicle.gasType,
            'description': vehicle.description,
            'image': vehicle.image,
            'status': vehicle.status
        }
    })

@app.route('/delete_vehicle/<int:vehicle_id>', methods=['POST'])
def delete_vehicle(vehicle_id):
    try:
        # Find the vehicle
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        
        # Get the image path
        upload_folder = app.config['UPLOAD_FOLDER']
        
        # Delete associated images
        if vehicle.image:
            try:
                # Remove main image
                main_image_path = os.path.join(upload_folder, vehicle.image)
                if os.path.exists(main_image_path):
                    os.remove(main_image_path)
                
                # Check for additional images
                additional_images_path = os.path.join(upload_folder, f"{vehicle_id}_additional")
                if os.path.exists(additional_images_path):
                    shutil.rmtree(additional_images_path)
            except Exception as e:
                logging.error(f"Error deleting images for vehicle {vehicle_id}: {e}")
        
        # Delete vehicle from database
        db.session.delete(vehicle)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Vehicle deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting vehicle {vehicle_id}: {e}")
        return jsonify({'success': False, 'message': 'Failed to delete vehicle'}), 500

@app.route('/clear_vehicles', methods=['POST'])
def clear_vehicles():
    try:
        # Delete all vehicles
        Vehicle.query.delete()
        db.session.commit()
        return jsonify({'message': 'All vehicles cleared successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Add route for category counts
@app.route('/get_category_counts', methods=['GET'])
def get_category_counts():
    try:
        # Query the database to count vehicles by category
        category_counts = db.session.query(
            Vehicle.category, 
            db.func.count(Vehicle.id)
        ).group_by(Vehicle.category).all()
        
        # Convert to dictionary
        counts = {category: count for category, count in category_counts}
        
        return jsonify(counts)
    except Exception as e:
        app.logger.error(f"Error getting category counts: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Booking Management Routes
@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    try:
        # Log the incoming booking data for debugging
        booking_data = request.json
        app.logger.info(f"Received booking data: {booking_data}")
        
        # Validate required fields with more lenient checks
        required_fields = [
            'customer_name', 'customer_email', 'customer_phone', 
            'vehicle_name', 'start_date', 'end_date', 
            'rental_days', 'base_rate', 'total_cost'
        ]
        
        for field in required_fields:
            if field not in booking_data or not str(booking_data[field]).strip():
                app.logger.error(f"Missing or empty required field: {field}")
                return jsonify({
                    'success': False, 
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Create a new booking in the database
        new_booking = Booking(
            customer_name=booking_data['customer_name'],
            customer_email=booking_data['customer_email'],
            customer_phone=booking_data['customer_phone'],
            vehicle_plate=booking_data.get('vehicle_plate', 'Unknown'),
            vehicle_name=booking_data['vehicle_name'],
            vehicle_category=booking_data.get('vehicle_category', 'Unknown'),
            start_date=datetime.strptime(booking_data['start_date'], '%Y-%m-%d'),
            end_date=datetime.strptime(booking_data['end_date'], '%Y-%m-%d'),
            rental_days=booking_data['rental_days'],
            base_rate=booking_data['base_rate'],
            additional_services=booking_data.get('additional_services', 0),
            total_cost=booking_data['total_cost'],
            status='Pending',  # Always set initial status to Pending
            status_notes='New booking created',
            additional_services_details=json.dumps(booking_data.get('additional_services_details', {}))
        )
        
        db.session.add(new_booking)
        db.session.commit()
        
        # Send real-time event for new booking
        booking_event_queue.put({
            'type': 'new_booking',
            'booking': {
                'id': new_booking.id,
                'customer_name': new_booking.customer_name,
                'vehicle_name': new_booking.vehicle_name,
                'start_date': new_booking.start_date.strftime('%Y-%m-%d'),
                'end_date': new_booking.end_date.strftime('%Y-%m-%d'),
                'total_cost': new_booking.total_cost,
                'status': new_booking.status
            }
        })
        
        return jsonify({
            'success': True, 
            'booking_id': new_booking.id, 
            'message': 'Booking submitted successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Booking submission error: {str(e)}")
        app.logger.error(f"Error details: {traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'message': f'Failed to submit booking: {str(e)}'
        }), 500

@app.route('/update_booking_status', methods=['POST'])
def update_booking_status():
    # Enhanced logging
    app.logger.info("Received booking status update request")
    app.logger.info(f"Request method: {request.method}")
    app.logger.info(f"Request content type: {request.content_type}")
    
    try:
        # Log raw request data
        raw_data = request.get_data()
        app.logger.info(f"Raw request data: {raw_data}")
        
        # Comprehensive parsing methods
        data = None
        parsing_methods = [
            lambda: request.get_json(force=True),
            lambda: request.get_json(),
            lambda: json.loads(raw_data.decode('utf-8')),
            lambda: request.form.to_dict() if request.form else None
        ]
        
        for method in parsing_methods:
            try:
                data = method()
                app.logger.info(f"Parsed data (method {method.__name__}): {data}")
                if data:
                    break
            except Exception as parse_error:
                app.logger.error(f"Parsing error with method {method.__name__}: {parse_error}")
        
        if not data:
            app.logger.error("Unable to parse request data")
            return jsonify({
                'success': False, 
                'message': 'Invalid request data. Please check your input.'
            }), 400
        
        # Validate required fields with more detailed logging
        required_fields = ['booking_id', 'status']
        for field in required_fields:
            if field not in data:
                app.logger.error(f"Missing required field: {field}")
                return jsonify({
                    'success': False, 
                    'message': f'Missing required field: {field}. Please provide all necessary information.'
                }), 400
        
        # Find the booking
        booking = Booking.query.get(data['booking_id'])
        if not booking:
            app.logger.error(f"Booking not found. ID: {data['booking_id']}")
            return jsonify({
                'success': False, 
                'message': 'Booking not found'
            }), 404
        
        # Update booking status without restrictions
        old_status = booking.status
        booking.status = data['status']
        booking.status_notes = data.get('notes', '')
        
        # Manage vehicle status based on booking status
        vehicle = Vehicle.query.filter_by(plate=booking.vehicle_plate).first()
        if vehicle:
            # Implement the specific rules for vehicle status
            if data['status'] in ['Cancelled', 'Completed', 'Pending']:
                vehicle.status = 'Available'
            elif data['status'] == 'Confirmed':
                vehicle.status = 'Booked'
            
            app.logger.info(f"Vehicle {vehicle.plate} status updated to {vehicle.status} based on booking status {data['status']}")
        
        # Commit changes
        db.session.commit()
        
        app.logger.info(f"Booking {booking.id} status updated from {old_status} to {booking.status}")
        
        return jsonify({
            'success': True, 
            'message': 'Booking status updated successfully',
            'vehicle_status': vehicle.status if vehicle else None
        }), 200
    
    except Exception as e:
        # Rollback in case of error
        db.session.rollback()
        
        # Log the full error
        app.logger.error(f"Error updating booking status: {str(e)}")
        app.logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False, 
            'message': f'Failed to update booking status: {str(e)}'
        }), 500

@app.route('/get_bookings', methods=['GET'])
def get_bookings():
    try:
        # Order bookings by ID in descending order (most recent first)
        bookings = Booking.query.order_by(Booking.id.desc()).all()
        booking_list = []
        
        for booking in bookings:
            booking_dict = {
                'id': str(booking.id),
                'customer_name': booking.customer_name,
                'customer_email': booking.customer_email,
                'customer_phone': booking.customer_phone,
                'vehicle_plate': booking.vehicle_plate,
                'vehicle_name': booking.vehicle_name,
                'vehicle_category': booking.vehicle_category,
                'start_date': booking.start_date.isoformat(),
                'end_date': booking.end_date.isoformat(),
                'rental_days': booking.rental_days,
                'base_rate': booking.base_rate,
                'additional_services': booking.additional_services,
                'total_cost': booking.total_cost,
                'status': booking.status,
                'status_notes': booking.status_notes,
                'additional_services_details': json.loads(booking.additional_services_details) if booking.additional_services_details else {}
            }
            booking_list.append(booking_dict)
        
        return jsonify(booking_list), 200
    
    except Exception as e:
        app.logger.error(f"Get bookings error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': 'Failed to retrieve bookings'
        }), 500

@app.route('/delete_booking', methods=['POST'])
def delete_booking():
    try:
        data = request.json
        booking = Booking.query.get(data['booking_id'])
        
        if not booking:
            return jsonify({
                'success': False, 
                'message': 'Booking not found'
            }), 404
        
        # Store booking details before deletion for event
        booking_details = {
            'id': booking.id,
            'customer_name': booking.customer_name,
            'vehicle_name': booking.vehicle_name
        }
        
        db.session.delete(booking)
        db.session.commit()
        
        # Send real-time event for booking deletion
        booking_event_queue.put({
            'type': 'booking_deleted',
            'booking': booking_details
        })
        
        return jsonify({
            'success': True, 
            'message': 'Booking deleted successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Delete booking error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': 'Failed to delete booking'
        }), 500

# Add route to serve sales_management.html
@app.route('/sales_management')
def sales_management():
    # Check if admin is authenticated
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    return send_file('sales_management.html')

# Comprehensive HTML Page and Static File Routing
@app.route('/<page>.html')
def serve_html_page(page):
    """
    Dynamically serve HTML pages with enhanced flexibility
    Supports multilingual, variations, and special pages
    """
    try:
        # Expanded list of valid pages with variations
        valid_pages = [
            # Base pages
            'index', 'index_en', 
            'rentals', 'rentals_en', 
            'sales', 'sales_en',
            'about', 'about_en',
            'contact', 'contact_en',
            'dashboard', 'dashboard_en',
            
            # Special pages
            'airport-transfer', 'airport-transfer_en',
            'admin-login',
            'bookings', 'bookings_en',
            'sales_management', 'sales_management_en',
            
            # Potential additional variations
            'services', 'services_en',
            'fleet', 'fleet_en'
        ]
        
        # Normalize page name to handle variations
        normalized_page = page.lower()
        
        # Check if requested page is valid
        if normalized_page not in valid_pages:
            app.logger.warning(f"Attempted to access invalid page: {page}")
            return render_template('index.html'), 404
        
        # Try to render the specific page, with fallback mechanisms
        try:
            # First, try exact match
            return render_template(f'{normalized_page}.html')
        except TemplateNotFound:
            # Fallback to base language or index
            fallback_pages = {
                'sales_en': 'sales.html',
                'about_en': 'about.html',
                'index_en': 'index.html',
                'rentals_en': 'rentals.html',
                'contact_en': 'contact.html',
                'dashboard_en': 'dashboard.html',
                'airport-transfer_en': 'airport-transfer.html',
                'bookings_en': 'bookings.html',
                'sales_management_en': 'sales_management.html'
            }
            
            if normalized_page in fallback_pages:
                try:
                    return render_template(fallback_pages[normalized_page])
                except TemplateNotFound:
                    pass
            
            # Final fallback to index
            app.logger.error(f"Template not found: {page}.html")
            return render_template('index.html'), 404
    
    except Exception as e:
        app.logger.error(f"Error serving page {page}: {e}")
        return render_template('index.html'), 500

# Enhanced Static File Serving with Comprehensive Support
@app.route('/<path:filename>')
def serve_static_or_page(filename):
    """
    Comprehensive static file and page serving
    Handles CSS, JS, images, HTML pages with advanced error logging
    """
    try:
        # Special handling for root route variations
        if filename in ['', 'index', 'home']:
            return index()
        
        # Check if it's a static file in static directories
        static_dirs = ['css', 'js', 'assets']
        for directory in static_dirs:
            file_path = os.path.join('static', directory, filename)
            if os.path.exists(file_path):
                return send_from_directory(f'static/{directory}', filename)
        
        # Check if it's an HTML page
        if filename.endswith('.html'):
            page_name = filename.replace('.html', '')
            return serve_html_page(page_name)
        
        # Additional handling for special routes
        special_routes = {
            'airport-transfer.html': 'services.html',
            'admin-login.html': 'dashboard.html',
            'bookings.html': 'rentals.html',
            'sales_management.html': 'dashboard.html'
        }
        
        if filename in special_routes:
            return render_template(special_routes[filename])
        
        # If no match found, log and return 404
        app.logger.warning(f"File not found: {filename}")
        return index(), 404
    
    except Exception as e:
        app.logger.error(f"Error serving {filename}: {e}")
        return index(), 500

# Ensure comprehensive file availability
def copy_html_files():
    """
    Ensure all HTML files are accessible for deployment
    Includes variations and special pages
    """
    import shutil
    
    html_files = [
        # Base pages
        'index.html', 'index_en.html',
        'rentals.html', 'rentals_en.html',
        'sales.html', 'sales_en.html',
        'about.html', 'about_en.html',
        'contact.html', 'contact_en.html',
        'dashboard.html', 'dashboard_en.html',
        
        # Special pages
        'airport-transfer.html', 'airport-transfer_en.html',
        'admin-login.html',
        'bookings.html', 'bookings_en.html',
        'sales_management.html', 'sales_management_en.html',
        
        # Additional pages
        'services.html', 'services_en.html',
        'fleet.html', 'fleet_en.html'
    ]
    
    for file in html_files:
        source = os.path.join(os.getcwd(), file)
        if not os.path.exists(source):
            app.logger.warning(f"HTML file not found: {file}")

# Initialize file management during app startup
with app.app_context():
    copy_html_files()
    app.logger.info("Comprehensive HTML file management initialized")

# Root Route with Comprehensive Handling
@app.route('/')
def index():
    """
    Serve the default index page with multiple fallback strategies
    """
    try:
        # Priority order for index pages
        index_pages = [
            'index.html',      # Default French version
            'index_en.html',   # English version fallback
            'rentals.html'     # Final fallback
        ]
        
        for page in index_pages:
            try:
                return render_template(page)
            except TemplateNotFound:
                app.logger.warning(f"Index page not found: {page}")
        
        # Absolute last resort
        return "Welcome to CarRent Comores", 200
    
    except Exception as e:
        app.logger.error(f"Critical error serving root route: {e}")
        return "Service Unavailable", 503

# Ensure index page is always available
def ensure_index_page():
    """
    Create minimal index page if not exists
    """
    import os
    
    index_files = [
        'index.html', 
        'index_en.html'
    ]
    
    for index_file in index_files:
        file_path = os.path.join(os.getcwd(), index_file)
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w') as f:
                    f.write(f"""
<!DOCTYPE html>
<html lang="{'en' if '_en' in index_file else 'fr'}">
<head>
    <meta charset="UTF-8">
    <title>CarRent Comores</title>
</head>
<body>
    <h1>Welcome to CarRent Comores</h1>
    <p>Temporary placeholder page</p>
</body>
</html>
""")
                app.logger.info(f"Created placeholder {index_file}")
            except Exception as e:
                app.logger.error(f"Failed to create {index_file}: {e}")

# Initialize index page during app startup
with app.app_context():
    ensure_index_page()
    app.logger.info("Index page initialization complete")

# Route to add a new sales vehicle
@app.route('/add_sales_vehicle', methods=['POST'])
def add_sales_vehicle():
    try:
        # Extract form data
        make = request.form.get('make')
        model = request.form.get('model')
        year = int(request.form.get('year'))
        category = request.form.get('category')
        condition = request.form.get('condition')
        price = float(request.form.get('price'))
        color = request.form.get('color')
        engine_size = request.form.get('engineSize')
        gas_type = request.form.get('gasType')
        drivetrain = request.form.get('drivetrain')
        plate_number = request.form.get('plateNumber')
        features = request.form.get('features', '')
        description = request.form.get('description')
        transmission = request.form.get('transmission')
        mileage = request.form.get('vehicleMileage')  # Changed from 'mileage'
        
        # Debug print
        print("\n--- DEBUG: Adding Sales Vehicle ---")
        print(f"Make: {make}")
        print(f"Model: {model}")
        print(f"Year: {year}")
        print(f"Price: {price}")
        print(f"Category: {category}")
        print("---\n")

        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            image_filename = save_uploaded_file(
                request.files['image'], 
                app.config['UPLOAD_FOLDER']
            )

        # Create new sales vehicle
        new_vehicle = SalesVehicle(
            make=make,
            model=model,
            year=year,
            category=category,
            condition=condition,
            price=price,
            color=color,
            engine_size=engine_size,
            gas_type=gas_type,
            drivetrain=drivetrain,
            plate_number=plate_number,
            features=features,
            description=description,
            transmission=transmission,
            mileage=int(mileage) if mileage and mileage.strip() else None,  # Convert to int if not empty
            image=image_filename
        )

        # Add to database
        db.session.add(new_vehicle)
        db.session.commit()

        # Print vehicles after adding
        print_sales_vehicles()

        return jsonify({
            'success': True, 
            'message': 'Vehicle added successfully',
            'vehicle': new_vehicle.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding sales vehicle: {str(e)}")
        print(f"Error adding sales vehicle: {str(e)}")
        return jsonify({
            'success': False, 
            'message': str(e)
        }), 500

# Route to get all sales vehicles
@app.route('/get_sales_vehicles', methods=['GET'])
def get_sales_vehicles():
    try:
        # Query all sales vehicles, ordered by most recent first
        vehicles = SalesVehicle.query.order_by(SalesVehicle.id.desc()).all()
        
        # Convert vehicles to list of dictionaries
        vehicles_list = [vehicle.to_dict() for vehicle in vehicles]
        
        # Log the number of vehicles for debugging
        app.logger.info(f"Fetched {len(vehicles_list)} sales vehicles")
        
        return jsonify(vehicles_list)
    except Exception as e:
        app.logger.error(f"Error retrieving sales vehicles: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve vehicles',
            'message': str(e)
        }), 500

# Comprehensive debug route for sales vehicles
@app.route('/debug/sales_vehicles', methods=['GET'])
def get_debug_sales_vehicles():
    try:
        # Query all sales vehicles
        vehicles = SalesVehicle.query.all()
        
        # Detailed vehicle information
        vehicles_details = []
        for vehicle in vehicles:
            vehicle_info = {
                'id': vehicle.id,
                'make': vehicle.make,
                'model': vehicle.model,
                'year': vehicle.year,
                'price': vehicle.price,
                'image': vehicle.image,
                'category': vehicle.category
            }
            vehicles_details.append(vehicle_info)
        
        # Log and return debug information
        app.logger.info(f"Debug: Found {len(vehicles_details)} sales vehicles")
        
        return jsonify({
            'total_vehicles': len(vehicles_details),
            'vehicles': vehicles_details
        })
    except Exception as e:
        app.logger.error(f"Error in debug sales vehicles route: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve debug information',
            'message': str(e)
        }), 500

# Route to get a single sales vehicle
@app.route('/get_sales_vehicle/<int:vehicle_id>')
def get_sales_vehicle(vehicle_id):
    try:
        vehicle = SalesVehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
            
        return jsonify(vehicle.to_dict())
    except Exception as e:
        logging.error(f"Error fetching sales vehicle: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Route to update a sales vehicle
@app.route('/update_sales_vehicle/<int:vehicle_id>', methods=['PUT'])
def update_sales_vehicle(vehicle_id):
    try:
        vehicle = SalesVehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404

        # Handle image upload
        if 'image' in request.files:
            # Delete old image if it exists
            if vehicle.image:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], vehicle.image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Save new image
            vehicle.image = save_uploaded_file(
                request.files['image'], 
                app.config['UPLOAD_FOLDER']
            )

        # Update vehicle details
        vehicle.make = request.form.get('make')
        vehicle.model = request.form.get('model')
        vehicle.year = int(request.form.get('year'))
        vehicle.category = request.form.get('category')
        vehicle.condition = request.form.get('condition')
        vehicle.price = float(request.form.get('price'))
        vehicle.color = request.form.get('color')
        vehicle.engine_size = request.form.get('engineSize')
        vehicle.gas_type = request.form.get('gasType')
        vehicle.drivetrain = request.form.get('drivetrain')
        vehicle.plate_number = request.form.get('plateNumber')
        vehicle.features = request.form.get('features')
        vehicle.description = request.form.get('description')
        vehicle.transmission = request.form.get('transmission')
        vehicle.mileage = int(request.form.get('vehicleMileage')) if request.form.get('vehicleMileage') and request.form.get('vehicleMileage').strip() else None

        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Vehicle updated successfully',
            'vehicle': vehicle.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating sales vehicle: {str(e)}")
        return jsonify({
            'success': False, 
            'message': str(e)
        }), 500

# Route to delete a sales vehicle
@app.route('/delete_sales_vehicle/<int:vehicle_id>', methods=['DELETE'])
def delete_sales_vehicle(vehicle_id):
    try:
        vehicle = SalesVehicle.query.get(vehicle_id)
        
        if not vehicle:
            return jsonify({
                'success': False, 
                'message': 'Vehicle not found'
            }), 404
        
        # Optional: Delete associated image file if it exists
        if vehicle.image:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], vehicle.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Delete the vehicle from the database
        db.session.delete(vehicle)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Vehicle deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting sales vehicle: {str(e)}")
        return jsonify({
            'success': False, 
            'message': str(e)
        }), 500

# Route to serve uploaded sales vehicle images
@app.route('/uploads/sales_vehicles/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Error handler for 404 errors
@app.errorhandler(404)
def page_not_found(e):
    app.logger.error(f"404 error: {request.url}")
    return jsonify({
        'error': 'Not Found',
        'message': f'The requested URL {request.url} was not found on this server.'
    }), 404

# Helper function to check if file is allowed
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to save uploaded file
def save_uploaded_file(file, upload_folder):
    filename = secure_filename(file.filename)
    unique_filename = f"{int(time.time())}_{filename}"
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    return unique_filename

# Debug method to print all sales vehicles
def print_sales_vehicles():
    try:
        vehicles = SalesVehicle.query.all()
        print("\n--- DEBUG: Sales Vehicles in Database ---")
        print(f"Total Vehicles: {len(vehicles)}")
        for vehicle in vehicles:
            print(f"ID: {vehicle.id}")
            print(f"Make: {vehicle.make}")
            print(f"Model: {vehicle.model}")
            print(f"Year: {vehicle.year}")
            print(f"Price: {vehicle.price}")
            print(f"Image: {vehicle.image}")
            print("---")
        print("--- END OF SALES VEHICLES ---\n")
    except Exception as e:
        print(f"Error printing sales vehicles: {str(e)}")

# Call this method after database operations for debugging
@app.route('/debug_sales_vehicles')
def debug_sales_vehicles():
    print_sales_vehicles()
    return jsonify({
        'message': 'Sales vehicles printed to console',
        'total_vehicles': len(SalesVehicle.query.all())
    })

@app.route('/check_vehicle_availability', methods=['POST'])
def check_vehicle_availability_route():
    """
    Flexible vehicle availability check that always returns True.
    Logs existing bookings for transparency.
    """
    data = request.json
    vehicle_name = data.get('vehicle_name')
    start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
    
    # Find existing bookings for the vehicle
    existing_bookings = Booking.query.filter(
        Booking.vehicle_name == vehicle_name,
        Booking.start_date <= end_date,
        Booking.end_date >= start_date
    ).all()
    
    # Log existing bookings for transparency
    if existing_bookings:
        app.logger.info(f"Multiple bookings exist for {vehicle_name} during the requested period:")
        for booking in existing_bookings:
            app.logger.info(f"Existing Booking - ID: {booking.id}, Status: {booking.status}, " 
                             f"Dates: {booking.start_date} to {booking.end_date}")
    
    # Always return True to allow booking
    return jsonify({
        'available': True,
        'existing_bookings_count': len(existing_bookings)
    })

if __name__ == '__main__':
    try:
        # Ensure upload directory exists with full permissions
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        os.chmod(upload_dir, 0o777)  # Full read, write, execute permissions

        # Create application context
        with app.app_context():
            # Create all database tables
            db.create_all()
            
            # Log database and environment information
            print("Database Configuration:")
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            print(f"Upload Folder: {upload_dir}")
            
            # Check database connection
            try:
                db.session.execute(text('SELECT 1'))
                print("Database connection successful")
            except Exception as db_error:
                print(f"Database connection error: {db_error}")
                raise

        # Run the application with detailed error handling
        print("Starting CarRent Application...")
        app.run(
            debug=True,  # Enables detailed error messages
            host='0.0.0.0',  # Listen on all available network interfaces
            port=5003,  # Changed from 5002 to 5003
            use_reloader=True  # Automatically reload on code changes
        )
    except Exception as startup_error:
        print(f"Fatal startup error: {startup_error}")
        print(traceback.format_exc())  # Print full stack trace
        raise  # Re-raise to ensure the error is not silently ignored
