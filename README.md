# AI Enhanced Car Pooling System

## Project Title

AI Enhanced Car Pooling System

---

## Project Overview

AI Enhanced Car Pooling System is an intelligent ride-sharing platform developed using Flask, SQLite, Machine Learning, and Generative AI. The system enables users to offer rides, search rides, book rides, receive ride recommendations, and view AI-generated trip summaries.

The application combines Full Stack Development, Machine Learning, and Generative AI to improve ride matching accuracy and user experience.

---

## Problem Statement

Daily commuters often struggle to find suitable ride-sharing partners with similar routes and schedules. Traditional carpooling systems provide limited intelligence in matching rides and explaining recommendations.

This project addresses the problem using Machine Learning based ride matching and AI-powered trip analysis.

---

## Objectives

- Simplify ride sharing
- Reduce travel costs
- Improve ride matching accuracy
- Provide AI-generated travel insights
- Encourage eco-friendly transportation

---

## Features

### User Management

- User Registration
- User Login & Logout
- Session Management
- Password Reset using OTP
- User Profile Management

### Ride Management

- Offer Ride
- Search Ride
- Book Ride
- Ride History
- Cancel Booking

### Machine Learning Features

- KNN Ride Matching
- Best Match Prediction
- Suitable Match Prediction
- Low Match Prediction
- Match Score Generation

### Generative AI Features

- AI Trip Summary
- Ride Compatibility Explanation
- Travel Insights
- AI Recommendation Description

### Additional Features

- Trust Score System
- Driver Badges
- Ride Demand Predictor
- Carbon Savings Calculator
- Analytics Dashboard

---

## Technologies Used

### Frontend

- HTML
- CSS
- Bootstrap
- JavaScript

### Backend

- Python
- Flask

### Database

- SQLite
- SQLAlchemy

### Machine Learning

- Scikit-Learn
- Pandas
- NumPy
- Joblib

### Generative AI

- Google Gemini API

---

## Project Structure

AI_CarPooling_Project/

├── Frontend/

├── Backend/

├── ML/

├── Documentation/

├── README.md

└── requirements.txt

---

## Database Setup

The project uses SQLite database.

Database file:

database.db

Tables include:

- Users
- Rides
- Bookings
- Notifications
- Ratings

---

## Machine Learning Module

### Workflow

Dataset
→ Data Preprocessing
→ Label Encoding
→ KNN Training
→ Model Evaluation
→ Model Saving (.pkl)
→ Flask Integration

### Model Used

K-Nearest Neighbors (KNN)

Purpose:

Ride Matching and Recommendation

---

## Generative AI Integration

Google Gemini API is used to generate:

- Trip Summaries
- Ride Explanations
- Travel Recommendations

### API Configuration

Create a .env file:

GEMINI_API_KEY=YOUR_API_KEY

---

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd AI_CarPooling_Project