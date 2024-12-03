# Egypt Metro Backend (Django)

## Overview

The **Egypt Metro Backend** provides the API and business logic for the **Egypt Metro** project. Built using **Django** and **Django REST Framework**, this backend handles user authentication, data storage, and real-time train schedules. It also serves APIs for the frontend (Flutter) and integrates with AI models for route optimization and crowd management.

## Features

- **User Authentication**: Secure login and registration with JWT.
- **API Endpoints**: Exposes endpoints for train schedules, routes, user profiles, and ticketing.
- **Real-Time Updates**: Provides real-time data on train locations, crowd levels, and schedules.
- **Payment Integration**: Handles secure payments for subscriptions and tickets.
- **Fault Reporting**: Allows users to report issues, with real-time admin updates.
- **Admin Dashboard**: Provides insights into ticket sales, user data, and performance.

## Installation

### Prerequisites
- Python 3.9+
- Django 3.x+
- PostgreSQL (or SQLite for local development)
- Django REST Framework

### Setup

1. **Clone the repository**:
     ```
     git clone https://github.com/egypt-metro/egypt-metro-backend.git
     ```
2. Navigate to the project directory:
    ```
    cd egypt-metro-backend
    ```
3. Create and activate a virtual environment:
   ```
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
4. Install dependencies:
   ```
    pip install -r requirements.txt
   ```
5. Set up the database:

   - Modify the database settings in settings.py if using PostgreSQL. For SQLite (default), no changes are needed.
   - Run migrations:
    ```
    python manage.py migrate
    ```
6. Create a superuser for the admin panel:
    ```
    python manage.py createsuperuser
    ```
7. Run the server:
    ```
    python manage.py runserver
    ```
8. Access the API at `http://localhost:8000/` and the admin panel at `http://localhost:8000/admin/`.

### API Endpoints
  - Authentication:
    - `POST /api/auth/register/`: User registration.
    - `POST /api/auth/login/`: User login (JWT token).
  - Routes and Schedules:
    - `GET /api/routes/`: List available metro routes.
    - `GET /api/schedules/`: Get real-time train schedules.
  - Tickets:
    - `POST /api/tickets/`: Create and view tickets.
  - User Profiles:
    - `GET /api/profile/`: View the user profile.
    - `PUT /api/profile/`: Update user profile.
  - Fault Reporting:
    - `POST /api/faults/`: Report a fault or issue.
    - `GET /api/faults/`: View reported faults.

### License
  - This project is licensed under the MIT License - see the LICENSE file for details.
