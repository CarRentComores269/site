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
import psycopg2

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),
                        logging.FileHandler('carrent_debug.log')
                    ])

# Create Flask app with explicit template and static folders
app = Flask(__name__, template_folder='.', static_folder='.')
app.secret_key = '3c0c195669557779ded02677b11ab02e'

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://carrent:1VdaCIodZYkjDO2jcZbpzvQccrV1VbwM@dpg-cv37t00gph6c738mkgvg-a.oregon-postgres.render.com/carrent_db_gyvr'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/sales_vehicles'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

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

# Add database backup functionality
import shutil
from datetime import datetime

def backup_database(db_path='carrent.db'):
    """
    Create a backup of the SQLite database
    
    Args:
        db_path (str): Path to the database file
    """
    try:
        # Create backups directory if it doesn't exist
        backup_dir = 'database_backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f'{backup_dir}/carrent_backup_{timestamp}.db'
        
        # Copy the database file
        shutil.copy2(db_path, backup_filename)
        
        print(f"Database backed up successfully: {backup_filename}")
        return backup_filename
    except Exception as e:
        print(f"Error creating database backup: {e}")
        return None

# Create tables
with app.app_context():
    # Remove db.drop_all() to preserve existing data
    
    # Recreate tables only if they don't exist
    db.create_all()
    
    # Optional: Add a print statement to confirm table creation
    print("Database tables ensured to exist.")
    
    # Automatically create a backup when the application starts
    backup_database()

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

# Route to serve the index page
@app.route('/')
def index():
    return render_template('index.html')

# Route to get vehicles
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
    } for v in vehicles])

# Route to serve sales management page
@app.route('/sales_management')
def sales_management():
    return render_template('sales_management.html')

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
