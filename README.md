# Egypt Metro Backend

<!-- ![Egypt Metro Logo](static/favicon.ico) -->

## System Status

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Status](https://img.shields.io/badge/status-operational-brightgreen)
![Uptime](https://img.shields.io/badge/uptime-96d%2019h%2021m-green)
![License](https://img.shields.io/badge/license-MIT-green)

## Technology Stack

![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.1.3-brightgreen)
![Django REST Framework](https://img.shields.io/badge/django%20rest%20framework-3.14.0-blue)
![PostgreSQL](https://img.shields.io/badge/postgresql-15.4-blue)
![Docker](https://img.shields.io/badge/docker-20.10.24-blue)
![Render](https://img.shields.io/badge/render-1.0.0-blue)
![API Endpoints](https://img.shields.io/badge/endpoints-60-orange)

## GitHub Metrics

![GitHub Stars](https://img.shields.io/github/stars/Egypt-Metro/backend?style=social)
![GitHub Forks](https://img.shields.io/github/forks/Egypt-Metro/backend?style=social)
![GitHub Issues](https://img.shields.io/github/issues/Egypt-Metro/backend)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/Egypt-Metro/backend)
![GitHub Last Commit](https://img.shields.io/github/last-commit/Egypt-Metro/backend)
![GitHub Language Count](https://img.shields.io/github/languages/count/Egypt-Metro/backend)
![GitHub Top Language](https://img.shields.io/github/languages/top/Egypt-Metro/backend)

<!-- The backend APIs for Egypt Metro platform.

**Live API:** [https://backend-54v5.onrender.com/](https://backend-54v5.onrender.com/) -->

## Table of Contents

- [Overview](#overview)
- [Related Projects](#related-projects)
- [Features](#features)
- [API Documentation](#api-documentation)
- [API Endpoints](#api-endpoints)
  - [Authentication](#authentication)
  - [Stations](#stations)
  - [Trains](#trains)
  - [Routes](#routes)
  - [Tickets](#tickets)
  - [Subscriptions](#subscriptions)
  - [Wallet](#wallet)
  - [System](#system)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Contact](#contact)

## Overview

The **Egypt Metro Backend API** provides a robust infrastructure for managing and operating the Egypt Metro platform. It serves as the central system for user authentication, station management, trip details, ticketing, subscriptions, payments, and real-time train information. The API is designed to support millions of daily passengers with high reliability and scalability.

## Related Projects

- **Frontend (Mobile App)**: [https://github.com/Egypt-Metro/frontend](https://github.com/Egypt-Metro/frontend) - Flutter-based mobile application
- **AI Models**: [https://github.com/Egypt-Metro/ai](https://github.com/Egypt-Metro/ai) - Machine learning models for crowd management.

## Features

### Passenger Features

- `User Authentication and Profile Management`: Secure user registration, login, and profile management.
- `Station Management`: Nearest station lookup and station list.
- `Trip Details`: Provide trip route, number of stations, ticket price, and average time.
- `Real-Time Train Details`: Provide real-time schedule data, including arrival times and crowd data for each car in train.
- `User Profiles`: Manage user accounts, including registration, login, subscription types, and payment options.
- `Online Ticketing`: Buy and generate tickets online with QR codes for easy scanning at metro gates.
- `Online Subscription`: Subscribe to or renew metro plans online.
- `Payment Options`: Users can pay via credit/debit cards, e-wallets, or other payment gateways.
- `Chatbot Support`: 24/7 AI-powered chatbot to answer questions, guide users, and connect with customer service.
- `Real-Time Updates`: Supports extensions for real-time data (e.g., train locations, crowd levels).

### Admin Features

- `Admin Dashboard`: Track sales and revenue for each line and station in real-time.
- `Fault Reporting`: Allow admins to view, respond to, and track the status of user-reported issues.
<!-- - `Revenue and Sales Tracking`: Monitor ticket sales and subscription renewals for each metro line and station.
- `Train Monitoring`: Track train locations and details in real-time. -->

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: [https://backend-54v5.onrender.com/swagger/](https://backend-54v5.onrender.com/swagger/)
- **ReDoc**: [https://backend-54v5.onrender.com/redoc/](https://backend-54v5.onrender.com/redoc/)
- **Swagger JSON**: [https://backend-54v5.onrender.com/swagger.json](https://backend-54v5.onrender.com/swagger.json)
- **API Schema**: [https://backend-54v5.onrender.com/api/schema/](https://backend-54v5.onrender.com/api/schema/)
- **API Docs**: [https://backend-54v5.onrender.com/api/docs/](https://backend-54v5.onrender.com/api/docs/)

## Technologies Used

- **Backend Framework**: Django
- **API**: Django REST Framework
- **Database**: PostgreSQL (hosted on Render)
- **Authentication**: JWT (JSON Web Token), Django Allauth
- **Documentation**: Swagger (DRF-YASG), ReDoc
- **Profiling**: Silk (development only)
- **Real-time Features**: WebSockets (optional, for live updates like train location or crowds)

## API Endpoints

The API provides 60 endpoints across 9 categories. Below is a summary of the main endpoints:

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/login/` | User authentication |
| GET | `/api/users/register/` | New user registration |
| GET | `/api/users/profile/` | Get user profile |
| GET | `/api/users/profile/update/` | Update user profile |
| GET | `/api/users/token/refresh/` | Refresh authentication token |
| GET | `/api/auth/password/reset/request/` | Request password reset |
| GET | `/api/auth/password/reset/confirm/` | Confirm password reset |
| GET | `/api/auth/password/reset/validate/` | Validate password reset token |

### Stations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stations/list/` | List all stations |
| GET | `/api/stations/nearest/` | Find nearest stations |
| GET | `/api/stations/trip/{start_station_id}/{end_station_id}/` | Get trip details between stations |

### Trains

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trains/` | List all trains |
| GET | `/api/trains/{train_id}/` | Get train details |
| GET | `/api/trains/get-schedules/` | Get train schedules |
| GET | `/api/trains/{train_id}/crowd-status/` | Get crowd status for a train |
| GET | `/api/trains/{train_id}/update-crowd-level/` | Update crowd level information |
| GET | `/api/trains/{train_id}/update-location/` | Update train location |
| GET | `/api/trains/{train_id}/station-schedule/` | Get station schedule for a train |
| GET | `/api/trains/debug/` | Debug information for trains |

### Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/routes/find/` | Find optimal routes between stations |

### Tickets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tickets/` | List user tickets |
| GET | `/api/tickets/{ticket_id}/` | Get ticket details |
| GET | `/api/tickets/purchase-with-wallet/` | Purchase ticket using wallet |
| GET | `/api/tickets/{ticket_id}/validate_entry/` | Validate ticket for entry |
| GET | `/api/tickets/{ticket_id}/validate_exit/` | Validate ticket for exit |
| GET | `/api/tickets/{ticket_id}/upgrade/` | Upgrade ticket |
| GET | `/api/tickets/{ticket_id}/upgrade-with-wallet/` | Upgrade ticket using wallet |
| GET | `/api/tickets/sync/` | Synchronize tickets |
| GET | `/api/tickets/types/` | List ticket types |
| GET | `/api/tickets/validate-scan/` | Validate ticket scan |
| GET | `/api/tickets/pending-upgrades/` | List pending ticket upgrades |
| GET | `/api/tickets/dashboard/` | Ticket dashboard |
| GET | `/api/tickets/gate-status/` | Get gate status |
| GET | `/api/tickets/hardware-status/` | Get hardware status |
| GET | `/api/tickets/scanner/process/` | Process scanner information |

### Subscriptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tickets/subscriptions/` | List user subscriptions |
| GET | `/api/tickets/subscriptions/{subscription_id}/` | Get subscription details |
| GET | `/api/tickets/subscriptions/active/` | Get active subscriptions |
| GET | `/api/tickets/subscriptions/purchase-with-wallet/` | Purchase subscription using wallet |
| GET | `/api/tickets/subscriptions/recommend/` | Get subscription recommendations |
| GET | `/api/tickets/subscriptions/{subscription_id}/cancel/` | Cancel subscription |
| GET | `/api/tickets/subscriptions/{subscription_id}/qr_code/` | Get subscription QR code |
| GET | `/api/tickets/subscriptions/{subscription_id}/validate_station/` | Validate subscription at station |

### Wallet

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wallet/wallet/my_wallet/` | Get user wallet |
| GET | `/api/wallet/wallet/add_funds/` | Add funds to wallet |
| GET | `/api/wallet/wallet/withdraw_funds/` | Withdraw funds from wallet |
| GET | `/api/wallet/transactions/` | List wallet transactions |
| GET | `/api/wallet/transactions/{transaction_id}/` | Get transaction details |
| GET | `/api/wallet/transactions/recent/` | Get recent transactions |
| GET | `/api/wallet/transactions/filter/` | Filter transactions |
| GET | `/api/wallet/payment-methods/` | List payment methods |
| GET | `/api/wallet/payment-methods/{payment_method_id}/` | Get payment method details |
| GET | `/api/wallet/payment-methods/{payment_method_id}/set_default/` | Set default payment method |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/` | System health check |

## Technology Details

### Backend Core

- **Framework**: Django 5.1.3
- **API Framework**: Django REST Framework 3.14.0
- **Database**: PostgreSQL 15.4
- **Cache**: Redis
- **Task Queue**: Celery
- **Web Server**: Gunicorn with Nginx

### Authentication & Security

- **Authentication**: JWT (JSON Web Tokens)
- **Security**: HTTPS, CORS, Input Validation
- **Password Hashing**: Argon2
- **Rate Limiting**: Django-ratelimit

### AI Integration

- **Machine Learning Integration**: REST API to AI services
- **Crowd Management Models**: Integration with Python-based ML models

### Payment Processing

- **Payment Gateway Integration**: Multiple payment providers
- **Digital Wallet**: Custom implementation with transaction history
- **Subscription Management**: Recurring payment handling

### DevOps & Monitoring

- **Deployment**: Render
- **Containerization**: Docker 20.10.24
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus with Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

### Testing & Documentation

- **Testing**: Pytest, Django Test Framework
- **API Documentation**: Swagger, ReDoc
- **Code Quality**: Black, Flake8, isort
- **Type Checking**: mypy

## Installation

### Prerequisites

- Python 3.12+
- PostgreSQL 15.4+
- Redis (optional, for caching and Celery)
- Git

### Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/Egypt-Metro/backend.git
   cd backend
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the root directory with the following variables:

   ```bash
   SECRET_KEY=your_secret_key
   DEBUG=True
   DATABASE_URL=postgres://user:password@localhost:5432/egypt_metro
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Run migrations**

   ```bash
   python manage.py migrate
   ```

6. **Create superuser (admin)**

   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**

   ```bash
   python manage.py runserver
   ```

8. **Access the API**:

   - API: `http://127.0.0.1:8000/`
   - Admin interface: `http://127.0.0.1:8000/admin/`
   - API documentation: `http://127.0.0.1:8000/swagger/`

## Deployment

The API is deployed on Render at [https://backend-54v5.onrender.com/](https://backend-54v5.onrender.com/)

For deployment to your own Render instance:

1. Create a new Web Service on Render
2. Connect to your GitHub repository
3. Set the following:
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - Start Command: `gunicorn config.wsgi:application`
4. Add the required environment variables
5. Deploy the service

## Contributing

We welcome contributions to the Egypt Metro Backend! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For inquiries, Feel free to reach out Me:

- Email: [a.moh.nassar00@gmail.com](mailto:a.moh.nassar00@gmail.com)
- GitHub: [AhmedNassar7](https://github.com/AhmedNassar7)

---

© 2025 Egypt Metro. All rights reserved.
