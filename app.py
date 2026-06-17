"""
Automobile Manufacturing Management System - Main Application
2-Tier Architecture: Application Tier + Database Tier
Phase 1: Manual AWS Deployment
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pymysql
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'automobile-mfg-dev-key')

# Database configuration - read from environment variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'admin'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'automobile_mfg'),
    'cursorclass': pymysql.cursors.DictCursor,
    'connect_timeout': 10
}

def get_db_connection():
    """Create and return a database connection"""
    return pymysql.connect(**DB_CONFIG)

def init_db():
    """Initialize database tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create vehicles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                vehicle_name VARCHAR(100) NOT NULL,
                vehicle_type VARCHAR(50) NOT NULL,
                manufacturing_date DATE,
                status VARCHAR(30) DEFAULT 'In Production',
                engine_capacity VARCHAR(20),
                color VARCHAR(30),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create production line table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS production_line (
                id INT AUTO_INCREMENT PRIMARY KEY,
                line_name VARCHAR(100) NOT NULL,
                vehicle_id INT,
                stage VARCHAR(50) NOT NULL,
                status VARCHAR(30) DEFAULT 'Active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL
            )
        ''')
        
        # Create inventory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                part_name VARCHAR(100) NOT NULL,
                part_number VARCHAR(50) UNIQUE NOT NULL,
                quantity INT DEFAULT 0,
                min_threshold INT DEFAULT 10,
                supplier VARCHAR(100),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # Create quality control table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_control (
                id INT AUTO_INCREMENT PRIMARY KEY,
                vehicle_id INT,
                inspector_name VARCHAR(100),
                check_date DATE,
                status VARCHAR(30) DEFAULT 'Pending',
                defects_found TEXT,
                passed BOOLEAN DEFAULT FALSE,
                comments TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database tables created/verified successfully!")
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

@app.route('/')
def index():
    """Home page - Dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get counts for dashboard
        cursor.execute('SELECT COUNT(*) as total FROM vehicles')
        vehicle_count = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM vehicles WHERE status='Completed'")
        completed_count = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM production_line WHERE status='Active'")
        active_lines = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM inventory WHERE quantity < min_threshold")
        low_stock = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        return render_template('index.html', 
                             vehicle_count=vehicle_count,
                             completed_count=completed_count,
                             active_lines=active_lines,
                             low_stock=low_stock)
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'error')
        return render_template('index.html', 
                             vehicle_count=0, completed_count=0,
                             active_lines=0, low_stock=0)

# ==================== VEHICLE MANAGEMENT ====================

@app.route('/vehicles')
def vehicles():
    """List all vehicles"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vehicles ORDER BY created_at DESC')
        vehicle_list = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('vehicles.html', vehicles=vehicle_list)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('vehicles.html', vehicles=[])

@app.route('/vehicles/add', methods=['GET', 'POST'])
def add_vehicle():
    """Add a new vehicle"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO vehicles (vehicle_name, vehicle_type, manufacturing_date, status, engine_capacity, color) VALUES (%s, %s, %s, %s, %s, %s)',
                (request.form['vehicle_name'], request.form['vehicle_type'],
                 request.form['manufacturing_date'], request.form['status'],
                 request.form['engine_capacity'], request.form['color'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Vehicle added successfully!', 'success')
            return redirect(url_for('vehicles'))
        except Exception as e:
            flash(f'Error adding vehicle: {str(e)}', 'error')
    return render_template('add_vehicle.html')

@app.route('/vehicles/update/<int:id>', methods=['GET', 'POST'])
def update_vehicle(id):
    """Update vehicle status"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE vehicles SET status=%s WHERE id=%s',
                (request.form['status'], id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Vehicle updated successfully!', 'success')
            return redirect(url_for('vehicles'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('vehicles'))

# ==================== PRODUCTION LINE ====================

@app.route('/production')
def production():
    """View production lines"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pl.*, v.vehicle_name 
            FROM production_line pl 
            LEFT JOIN vehicles v ON pl.vehicle_id = v.id 
            ORDER BY pl.started_at DESC
        ''')
        lines = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('production.html', production_lines=lines)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('production.html', production_lines=[])

@app.route('/production/start', methods=['POST'])
def start_production():
    """Start a new production line"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO production_line (line_name, vehicle_id, stage, status) VALUES (%s, %s, %s, %s)',
            (request.form['line_name'], request.form['vehicle_id'],
             request.form['stage'], 'Active')
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Production line started!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('production'))

@app.route('/production/complete/<int:id>', methods=['POST'])
def complete_production(id):
    """Mark production line as complete"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            'UPDATE production_line SET status=%s, completed_at=%s WHERE id=%s',
            ('Completed', now, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Production completed!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('production'))

# ==================== INVENTORY ====================

@app.route('/inventory')
def inventory():
    """View inventory"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inventory ORDER BY part_name')
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('inventory.html', inventory=items)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('inventory.html', inventory=[])

@app.route('/inventory/add', methods=['POST'])
def add_inventory():
    """Add inventory item"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO inventory (part_name, part_number, quantity, min_threshold, supplier) VALUES (%s, %s, %s, %s, %s)',
            (request.form['part_name'], request.form['part_number'],
             int(request.form['quantity']), int(request.form['min_threshold']),
             request.form['supplier'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Inventory item added!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('inventory'))

@app.route('/inventory/update/<int:id>', methods=['POST'])
def update_inventory(id):
    """Update inventory quantity"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE inventory SET quantity=%s WHERE id=%s',
            (int(request.form['quantity']), id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Inventory updated!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('inventory'))

# ==================== QUALITY CONTROL ====================

@app.route('/quality')
def quality():
    """View quality control records"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT qc.*, v.vehicle_name 
            FROM quality_control qc 
            LEFT JOIN vehicles v ON qc.vehicle_id = v.id 
            ORDER BY qc.check_date DESC
        ''')
        records = cursor.fetchall()
        
        # Get vehicles for dropdown
        cursor.execute('SELECT id, vehicle_name FROM vehicles WHERE status="In Production"')
        available_vehicles = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('quality.html', quality_records=records, vehicles=available_vehicles)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('quality.html', quality_records=[], vehicles=[])

@app.route('/quality/add', methods=['POST'])
def add_quality_check():
    """Add quality control check"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        passed = request.form.get('passed') == 'on'
        cursor.execute(
            'INSERT INTO quality_control (vehicle_id, inspector_name, check_date, status, defects_found, passed, comments) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (request.form['vehicle_id'], request.form['inspector_name'],
             request.form['check_date'], request.form['status'],
             request.form.get('defects_found', ''), passed,
             request.form.get('comments', ''))
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Quality check recorded!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('quality'))

# ==================== API ENDPOINTS (for health checks, monitoring) ====================

@app.route('/api/health')
def health_check():
    """Health check endpoint for ALB target group"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 as status')
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return jsonify({'status': 'healthy', 'database': 'connected', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e), 'timestamp': datetime.now().isoformat()}), 500

@app.route('/api/dashboard')
def dashboard_api():
    """API endpoint for dashboard data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM vehicles')
        vehicles = cursor.fetchone()['total']
        
        cursor.execute('SELECT vehicle_type, COUNT(*) as count FROM vehicles GROUP BY vehicle_type')
        by_type = cursor.fetchall()
        
        cursor.execute('SELECT status, COUNT(*) as count FROM production_line GROUP BY status')
        production_status = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'vehicles': vehicles,
            'by_type': by_type,
            'production_status': production_status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    # For production, use gunicorn: gunicorn -b 0.0.0.0:5000 app:app
    app.run(host='0.0.0.0', port=5000, debug=True)
