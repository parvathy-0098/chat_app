# Overview

This is a Flask-based secure messaging application called "SecureChat" that provides end-to-end encrypted messaging using RSA-2048 encryption. The application allows users to register, verify their email, generate encryption keys, and send secure messages that can only be decrypted by the intended recipient. It features user authentication, message encryption/decryption, and a web interface for secure communications.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask web application with session-based authentication
- **Encryption**: RSA-2048 end-to-end encryption for all messages
- **Storage**: PostgreSQL database with SQLAlchemy ORM for persistent data storage
- **Email Integration**: Flask-Mail for email verification during registration
- **Authentication**: Session-based user authentication with password hashing

## Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme
- **UI Framework**: Bootstrap 5 with Feather icons for consistent iconography
- **JavaScript**: Vanilla JS for encryption/decryption operations and UI interactions
- **Responsive Design**: Mobile-first approach with responsive grid layouts

## Core Services Architecture
- **CryptoUtils**: Handles RSA key generation, encryption, and decryption operations
- **IdentityVerifier**: Manages email verification codes and SMTP email sending
- **User Management**: Registration, login, logout with secure password hashing
- **Message System**: Encrypted message storage and retrieval with recipient verification

## Database Schema
- **Users Table**: Stores user accounts with email, password hash, RSA keys, and auto-verification status
- **Messages Table**: Contains encrypted messages with sender/recipient relationships and timestamps
- **VerificationCodes Table**: Legacy table for email verification (no longer used in simplified flow)

## Data Flow
1. User registers with email and password (stored in PostgreSQL)
2. Account is immediately activated and RSA key pair generated
3. User is auto-logged in and redirected to chat messages
4. User can send encrypted messages to other users
5. Messages encrypted with recipient's public key before database storage
6. Recipients decrypt messages with their private key from database
7. Session management for authenticated users with persistent storage

## Security Features
- RSA-2048 encryption for all messages
- Secure password hashing with Werkzeug
- Email verification for account activation
- Session-based authentication
- Private keys stored securely in user sessions

# External Dependencies

## Core APIs
- **Flask-Mail**: Email service for verification codes and notifications
- **RSA Cryptography**: End-to-end encryption using RSA-2048 keys
- **Flask Framework**: Web application foundation with routing and templating

## Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme support
- **Feather Icons**: Lightweight icon library for consistent iconography
- **JavaScript**: Vanilla JS for client-side encryption and UI functionality

## Python Dependencies
- **Flask**: Web framework and request handling
- **Flask-Mail**: Email sending capabilities for verification
- **Cryptography**: RSA key generation and encryption operations
- **Werkzeug**: Secure password hashing and session management
- **PyCryptodome**: Additional cryptographic functions

## Development Tools
- **Python Standard Library**: File handling, datetime, and system operations
- **Environment Variables**: Configuration management for email credentials and session secrets