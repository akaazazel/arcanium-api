# Arcanium API

<p align="center">
  <img width="200" height="200" src="/media/logo.png" alt="Arcanium API Logo">
</p>

<h3 align="center">Arcanium API</h3>

<div align="center">

![Status](https://img.shields.io/badge/status-active-success.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

</div>

---

<p align="center">
  A secure note management REST API built with FastAPI.
</p>

## Table of Contents

- [Arcanium API](#arcanium-api)
    - [Table of Contents](#table-of-contents)
    - [About](#about)
    - [Features](#features)
    - [Architecture](#architecture)
        - [Request Flow](#request-flow)
        - [Architecture Overview](#architecture-overview)
        - [Detailed Diagram](#detailed-diagram)
    - [Security Considerations](#security-considerations)
        - [Authentication \& Token Management](#authentication--token-management)
            - [Refresh Token Rotation](#refresh-token-rotation)
            - [Refresh Token Revocation](#refresh-token-revocation)
        - [Data Protection](#data-protection)
            - [Note Encryption](#note-encryption)
        - [Password Security](#password-security)
        - [Security Headers](#security-headers)
        - [Rate Limiting](#rate-limiting)
    - [Getting Started](#getting-started)
        - [Prerequisites](#prerequisites)
        - [Installation](#installation)
            - [1. Clone the repository](#1-clone-the-repository)
            - [2. Create an environment file](#2-create-an-environment-file)
            - [3. Build and start the application](#3-build-and-start-the-application)
        - [Accessing the API](#accessing-the-api)
    - [Running Tests](#running-tests)
    - [API Reference](#api-reference)
        - [Authentication](#authentication)
        - [Notes](#notes)
            - [`GET /notes` Query Parameters](#get-notes-query-parameters)
    - [Deployment](#deployment)
    - [Built With](#built-with)
        - [Backend Framework](#backend-framework)
        - [Programming Language](#programming-language)
        - [Database](#database)
        - [ORM \& Database Management](#orm--database-management)
        - [Security](#security)
        - [API Protection](#api-protection)
        - [Testing](#testing)
        - [DevOps \& Deployment](#devops--deployment)
    - [Author](#author)
    - [Known Limitations](#known-limitations)
    - [Acknowledgements](#acknowledgements)

---

## About

Arcanium API is a secure note management REST API that allows users to register, authenticate, and manage personal notes.

To protect user data, note contents are encrypted before being stored in the database. The API also includes JWT-based authentication, refresh token rotation, rate limiting, and security-focused middleware.

<!-- ### Demo -->

<!-- _Add screenshots, API documentation links, or deployment URLs here._ -->

---

## Features

- User registration and authentication
- JWT access and refresh tokens
- Refresh token rotation
- Secure password hashing
- Note encryption before storage
- Rate limiting with Redis and SlowAPI
- PostgreSQL persistence
- Automated database migrations with Alembic
- Comprehensive unit and integration testing
- Dockerized development environment

---

## Architecture

Every incoming request passes through a series of middleware components before reaching the application logic.

### Request Flow

![Arcanium API Architecture](/media/request_flow.png)

### Architecture Overview

- **Middleware Layer**
    - Handles CORS validation.
    - Applies request rate limiting using SlowAPI.
    - Adds security-related HTTP response headers.

- **Dependency Layer**
    - Provides database sessions.
    - Handles authentication and user retrieval.
    - Manages request-level dependencies.

- **Route Layer**
    - Processes incoming requests.
    - Validates request data.
    - Returns responses and HTTP exceptions.

- **Service Layer**
    - Contains the core business logic.
    - Performs database operations.
    - Coordinates interactions between different components.

- **Utility Layer**
    - Provides reusable helper functions.
    - Handles password hashing, token generation, token validation, and note encryption.

- **PostgreSQL**
    - Primary persistent data store.

- **Redis**
    - Stores revoked refresh tokens.
    - Used by SlowAPI for rate limiting.

### Detailed Diagram

![Arcanium API Architecture](/media/architecture.png)

---

## Security Considerations

### Authentication & Token Management

#### Refresh Token Rotation

The API implements refresh token rotation. New access and refresh tokens are issued during both login and token refresh operations.

This reduces the risk of long-term token misuse by limiting the lifetime of any individual refresh token.

#### Refresh Token Revocation

Refresh tokens can be revoked during logout.

Only refresh tokens are tracked and revoked. Access tokens are intentionally not stored or checked against a revocation list because:

- Access tokens have a short expiration time.
- Checking every access token against a database or cache on each request would introduce additional overhead.
- Revoking refresh tokens prevents attackers from obtaining new access tokens once a user logs out.

When a refresh token is used to request new tokens, its revocation status is verified before new tokens are issued.

### Data Protection

#### Note Encryption

Note contents are encrypted using Fernet symmetric encryption before being stored in the database.

- Stored note contents remain unreadable without the encryption key.
- Encrypting the same plaintext multiple times produces different ciphertext values due to random initialization vectors.
- Data can be securely decrypted when accessed by authorized users.

### Password Security

Passwords are never stored in plaintext.

The API uses Argon2id for password hashing, which is considered one of the strongest modern password hashing algorithms.

- One-way irreversible hashing.
- Automatic salt generation.
- Resistance against brute-force and GPU-based attacks.

### Security Headers

Custom middleware adds several security-related HTTP headers to API responses, including:

- `X-Content-Type-Options`
- `X-Frame-Options`
- `Strict-Transport-Security` (recommended for HTTPS deployments)

These headers help mitigate common attacks such as:

- MIME type sniffing
- Clickjacking
- Protocol downgrade attacks

### Rate Limiting

All API endpoints are protected by request rate limiting using SlowAPI and Redis.

Authentication-related endpoints use stricter limits than standard application routes to reduce the risk of:

- Credential stuffing
- Brute-force login attempts
- Automated abuse of authentication endpoints

---

## Getting Started

These instructions will help you run the project locally for development and testing.

### Prerequisites

The project requires:

- Docker Engine
- Docker Compose

Install Docker by following the official documentation:

https://docs.docker.com/get-docker/

### Installation

#### 1. Clone the repository

```bash
git clone https://github.com/akaazazel/arcanium-api.git
cd arcanium-api
```

#### 2. Create an environment file

Create a `.env` file in the project root using the provided `.env.example` as a reference.

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=postgres_db_name

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_password
REDIS_TOKEN_DB=0
REDIS_LIMITER_DB=1

SECRET_KEY=a881879338337a905f979fab8191a05bbba9874daf156c6c6271a61f6c3e426d
ENCRYPTION_KEY=77Z1hqpoiR_lYsmEB6PPspQKDkZJspt3RR3HiG7xsOY=
ALGORITHM=HS256
TOKEN_EXPIRY_MINUTES=5
TOKEN_EXPIRY_DAYS=30
```

#### 3. Build and start the application

```bash
docker compose build
docker compose up
```

Docker Compose will:

1. Start PostgreSQL.
2. Start Redis.
3. Wait until both services become healthy.
4. Launch the FastAPI application.

### Accessing the API

Application:

```text
http://localhost:8000
```

Interactive Documentation:

```text
http://localhost:8000/docs
```

OpenAPI Schema:

```text
http://localhost:8000/openapi.json
```

---

## Running Tests

The project includes tests for:

- Utilities
- Services
- API Routes

Run tests inside the FastAPI container:

```bash
python -m pytest
```

---

## API Reference

### Authentication

| Method | Endpoint         | Description                             |
| ------ | ---------------- | --------------------------------------- |
| POST   | `/auth/register` | Register a new user                     |
| POST   | `/auth/login`    | Authenticate a user                     |
| POST   | `/auth/logout`   | Revoke the current session              |
| POST   | `/auth/refresh`  | Generate a new access and refresh token |
| GET    | `/auth/me`       | Retrieve the current user's profile     |

### Notes

| Method | Endpoint           | Description              |
| ------ | ------------------ | ------------------------ |
| POST   | `/notes`           | Create a new note        |
| GET    | `/notes/{note_id}` | Retrieve a specific note |
| GET    | `/notes`           | Retrieve paginated notes |
| PUT    | `/notes/{note_id}` | Update a note            |
| DELETE | `/notes/{note_id}` | Delete a note            |

#### `GET /notes` Query Parameters

| Parameter     | Description                       |
| ------------- | --------------------------------- |
| `sort`        | `date_created` or `date_updated`  |
| `order`       | `asc` or `desc`                   |
| `limit`       | Number of records to return       |
| `offset_id`   | Last note ID from previous page   |
| `offset_date` | Last note date from previous page |

Pagination is implemented using cursor-based pagination to efficiently handle large datasets.

---

## Deployment

Before deploying to production, ensure that the following security header is enabled in the custom middleware:

```python
Strict-Transport-Security
```

It is disabled during local development to avoid issues when testing over HTTP.

Production deployment should always use HTTPS.

---

## Built With

### Backend Framework

- **FastAPI** – High-performance asynchronous web framework for building REST APIs.

### Programming Language

- **Python** – Core application language.

### Database

- **PostgreSQL** – Primary relational database for persistent storage.
- **Redis** – In-memory data store used for token revocation and rate limiting.

### ORM & Database Management

- **SQLAlchemy** – Asynchronous ORM and database toolkit.
- **Alembic** – Database migration and schema versioning tool.

### Security

- **JWT (JSON Web Tokens)** – Stateless authentication mechanism.
- **pwdlib** – Password hashing and verification.
- **Fernet Encryption** – Encryption of note contents before storage.

### API Protection

- **SlowAPI** – Request rate limiting integrated with Redis.

### Testing

- **PyTest** – Unit and integration testing framework.
- **pytest-asyncio** – Asynchronous test support for FastAPI and SQLAlchemy.

### DevOps & Deployment

- **Docker** – Containerized application deployment.
- **Docker Compose** – Multi-container orchestration for FastAPI, PostgreSQL, and Redis.

---

## Author

- GitHub: https://github.com/akaazazel

---

## Known Limitations

Building the test suite exposed several design decisions that made testing more difficult than necessary.

Some functions were written in a way that tightly coupled business logic, database access, and helper functionality. While this approach worked during development, it made isolated unit testing more challenging because individual pieces could not be tested independently as easily as they should have been.

If I were starting this project again, I would place greater emphasis on testability during the design phase. Related functionality would be encapsulated into dedicated classes and components with clearly defined responsibilities, making dependencies easier to mock and individual units easier to test.

Another improvement would be to spend more time designing the overall architecture before implementation begins. As the project evolved, several structures and patterns were refined through trial and error. Planning these components in advance would have reduced refactoring effort and produced a cleaner design from the start.

Despite these limitations, the challenges encountered during development and testing provided valuable experience in software architecture, dependency management, and test design. These lessons are already influencing how I approach new projects.

---

## Acknowledgements

Built independently as a portfolio project to apply and deepen practical skills in backend architecture, authentication design, API security, and containerized deployment.
