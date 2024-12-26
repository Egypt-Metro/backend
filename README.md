# Egypt Metro Backend API (Django)

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.1.3-brightgreen)

## Overview

The **Egypt Metro Backend** is a robust API, business logic, and metro administration for managing and operating the Egypt Metro platform. Built with **Django**, it provides seamless user authentication, station & lines management, trip details, route planning, real-time train schedules, online tickets & subscription management, and AI-powered features such as crowd prediction, route optimization, and Chatbot Support. The system efficiently handles approximately **4 million passengers daily**, ensuring scalability and reliability. The backend integrates with Flutter (frontend) and AI models, delivering a scalable and efficient solution.

---

## Features

### Passenger Features

- **User Authentication**: Registration, login, profile management, and JWT support.
- **Station Management**: Nearest station lookup, station list, and trip details.
- **Route and Trip Planning**: Manage metro routes, count the number of stations, and calculate ticket prices.
- **Train Schedules**: Provide real-time schedule data, including arrival times and GPS-tracked train locations.
- **Real-Time Crowd Management**: Use AI to predict train crowd levels and recommend less crowded options.
- **User Profiles**: Manage user accounts, including registration, login, subscription types, and payment options.
- **Online Ticketing**: Buy and generate tickets online with QR codes for easy scanning at metro gates
- **Online Subscription**: Subscribe to or renew metro plans online.
- **Payment Options**: Users can pay via credit/debit cards, e-wallets, or other payment gateways.
- **Chatbot Support**: 24/7 AI-powered chatbot to answer questions, guide users, and connect with customer service.
- **Real-Time Updates**: Supports extensions for real-time data (e.g., train locations, crowd levels).

### Admin Features

- **Admin Dashboard**: Track revenue, sales, and station performance in real-time.
- **Fault Reporting**: Allow admins to view, respond to, and track the status of user-reported issues.
- **Revenue and Sales Tracking**: Monitor ticket sales and subscription renewals for each metro line and station.
- **Train Monitoring**: Track train locations and details in real-time.

---

## Technologies Used

- **Backend Framework**: Django
- **API**: Django REST Framework
- **Database**: PostgreSQL (hosted on Render)
- **Authentication**: JWT (JSON Web Token), Django Allauth
- **Documentation**: Swagger (DRF-YASG), ReDoc
- **Profiling**: Silk (development only)
- **Real-time Features**: WebSockets (optional, for live updates like train location or crowds)

---

## Installation

### Prerequisites

- **Python**: Version 3.9+
- **Django**: Version 4.x+
- **PostgreSQL** (recommended for production)
- **Swagger & ReDoc**: For API documentation
- **Docker**: For containerized deployment (optional)
- **Poetry** or **Pip**: For managing dependencies
- **Channels**: for real-time updates

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Egypt-Metro/backend.git
   cd backend
   ```

2. **Set Up Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the root directory and add the following:

   ```env
   SECRET_KEY=<your-secret-key>
   DEBUG=True  # Set to False in production
   DB_NAME=<your-db-name>
   DB_USER=<your-db-user>
   DB_PASSWORD=<your-db-password>
   DB_HOST=<your-db-host>
   DB_PORT=5432
   ````

5. **Apply Migrations**

   ```bash
   python manage.py migrate
   ```

6. **Create Superuser**

   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Server**

   ```bash
   python manage.py runserver
   ```

8. **Access the API**:
   - API Base URL: `http://127.0.0.1:8000`
   - Admin Panel: `http://127.0.0.1:8000/admin/`

---

## API Endpoints

### Authentication Endpoints

| Method | Endpoint              | Description                 |
|--------|-----------------------|-----------------------------|
| POST   | `/api/users/register/` | Register a new user.         |
| POST   | `/api/users/login/`    | Login to get JWT tokens.     |
| POST   | `/api/users/token/refresh/` | Refresh access token.      |
| GET    | `/api/users/profile/`  | Retrieve user profile.       |
| PATCH  | `/api/users/profile/update/` | Update user profile.       |

### Metro Stations Endpoints

| Method | Endpoint                                         | Description                         |
|--------|--------------------------------------------------|-------------------------------------|
| GET    | `/api/stations/list/`                            | List all metro stations.            |
| GET    | `/api/stations/trip/<start_station_id>/<end_station_id>/` | Get trip details between two stations. |
| GET    | `/api/stations/nearest/`                         | Get the nearest metro station.      |

### Route and Trip Planning

| Method | Endpoint                                 | Description                                                        |
|--------|------------------------------------------|--------------------------------------------------------------------|
| GET    | `/api/routes/`                           | Get available routes and their respective details (stations, trip duration, price). |
| GET    | `/api/routes/{start_station}/{end_station}/` | Get a route between two stations, including trip details and fare. |

### Train Schedules

| Method | Endpoint                                 | Description                                                        |
|--------|------------------------------------------|--------------------------------------------------------------------|
| GET    | `/api/schedules/`                        | Get the current train schedules.                                   |
| GET    | `/api/schedules/{train_id}/`             | Get schedule details for a specific train.                         |

### User Management

| Method | Endpoint                                 | Description                                                        |
|--------|------------------------------------------|--------------------------------------------------------------------|
| POST   | `/api/users/register/`                  | Register a new user.                                               |
| POST   | `/api/users/login/`                     | Login a user.                                                      |
| GET    | `/api/users/{user_id}/`                  | Get user profile information.                                      |

### Ticketing

| Method | Endpoint                                 | Description                                                        |
|--------|------------------------------------------|--------------------------------------------------------------------|
| POST   | `/api/tickets/`                          | Create a new ticket based on the route selected.                    |
| GET    | `/api/tickets/{ticket_id}/`              | Get ticket details.                                                |

### Miscellaneous Endpoints

| Method | Endpoint      | Description                  |
|--------|---------------|------------------------------|
| GET    | `/health/`    | Health check for the API.    |

---

## API Documentation

Interactive API documentation is available:

- **Swagger UI**: [https://backend-54v5.onrender.com/swagger/](https://backend-54v5.onrender.com/swagger/)
- **ReDoc**: [https://backend-54v5.onrender.com/redoc/](https://backend-54v5.onrender.com/redoc/)
- **Swagger JSON**: [https://backend-54v5.onrender.com/swagger.json](https://backend-54v5.onrender.com/swagger.json)

---

## Deployment

The project is deployed using **Render**. To deploy:

1. **Configure Environment Variables** on Render.
2. Use the provided PostgreSQL database settings.
3. Deploy the Django app with the necessary build and start commands.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For inquiries, please reach out to **Ahmed Nassar**:

- Email: [a.moh.nassar00@gmail.com](mailto:a.moh.nassar00@gmail.com)
- GitHub: [AhmedNassar7](https://github.com/AhmedNassar7)
