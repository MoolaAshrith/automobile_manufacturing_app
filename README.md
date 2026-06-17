# Automobile Manufacturing Management System

Python Flask application for managing vehicle models, manufacturing plants,
production orders, inventory parts, assembly status, and quality inspections.

## Features

- Dashboard with production and inventory summary
- Vehicle model management
- Manufacturing plant management
- Production order tracking
- Inventory part tracking with low-stock alerts
- Assembly stage status tracking
- Quality inspection records

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

The app uses SQLite locally and creates `automobile.db` automatically.

## AWS EC2 / RDS MySQL Notes

Install requirements on EC2:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables for RDS:

```bash
export DB_TYPE=mysql
export DB_HOST=your-rds-endpoint.amazonaws.com
export DB_PORT=3306
export DB_NAME=automobile_manufacturing
export DB_USER=admin
export DB_PASSWORD='your-password'
export FLASK_SECRET_KEY='change-this-secret'
```

Run:

```bash
python app.py
```

For production, run behind Gunicorn and Nginx:

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

Security group recommendation:

- ALB: allow HTTP/HTTPS from the internet
- EC2: allow app traffic only from the ALB security group
- RDS: allow MySQL port 3306 only from the EC2 security group

