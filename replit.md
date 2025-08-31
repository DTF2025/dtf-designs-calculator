# Replit.md

## Overview

This is a Flask-based customer quoting application for DTF Designs that calculates pricing for wide format printing products. The system provides a customer-facing interface with detailed cost calculations based on materials, finishing options, and coverage levels.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web application with Python
- **Structure**: Modular design with separate configuration management
- **Routing**: Single customer-facing quote generator interface
- **Calculation Engine**: Area-based pricing system for print products with support for finishing options

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask
- **UI Framework**: Bootstrap 5 with dark theme
- **Forms**: Server-side form processing with real-time category switching
- **Responsive Design**: Mobile-friendly interface with grid layouts

### Data Management
- **Configuration**: Embedded JSON-like configuration in Python dictionaries
- **Product Catalog**: In-memory catalog with media types, pricing tiers, and finishing options
- **No Database**: All data stored in configuration files for simplicity

### Pricing System
- **Cost Components**: Media cost, equipment overhead, ink coverage, labor, and finishing options
- **Customer Tiers**: Retail, wholesale, and partner pricing with different discount structures
- **Calculation Types**: Area-based (per square foot) and per-unit pricing models
- **Finishing Options**: Hemming, grommets, lamination with automatic cost calculations

### Security & Session Management
- **Session Handling**: Flask sessions with configurable secret key
- **Environment Variables**: Support for production environment configuration
- **Input Validation**: Form data validation and error handling

## External Dependencies

### Python Packages
- **Flask**: Web framework for routing and templating
- **Standard Library**: os, math, logging for core functionality

### Frontend Libraries
- **Bootstrap 5**: UI framework loaded via CDN
- **Bootstrap JavaScript**: Component functionality and interactions

### Development Tools
- **Flask Development Server**: Built-in development server with debug mode
- **Python Logging**: Debug-level logging for development

### Media Catalog
- Physical print media from vendors like Ultraflex, Avery, Alpha, and Nekoosa
- Pre-configured with cost per square foot and material types

### Potential Integrations
- Environment-based configuration for production deployment
- Rate limiting and security headers for production use
- Payment processing integration points available