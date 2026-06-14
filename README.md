# TastyTrove 🍽️

TastyTrove is a recipe discovery and sharing web app built with Flask and SQLite, featuring AI-powered recipe recommendations. Users can browse recipes by category, search, rate dishes, view detailed cooking instructions, and submit their own recipes.

Live Demo: https://tastytrove-a-recipe-sharing-platform-2.onrender.com/

# Features

- Browse & Search Recipes – Explore recipes across categories like Breakfast, Desserts, Snacks & Fast Foods, and Drinks, with live search filtering.
- Recipe Details – View ingredients, step-by-step instructions, prep time, ratings, and video tutorials (English & Malayalam).
- Rating System – Rate recipes (1–5 stars); average ratings update dynamically.
- AI-Powered Recommendations – "You might also like" suggestions powered by a TF-IDF content-based recommender (ml_models.py), recomputed whenever recipes or ratings change.
- Recipe Submission – Users can submit their own recipes with images, which are automatically added to the database and made searchable/recommendable.

# Tech Stack

- Backend: Flask, Flask-SQLAlchemy
- Database: SQLite
- Machine Learning: Custom TF-IDF recommender (ml_models.py)
- Frontend: HTML, CSS, JavaScript

# Getting Started

# Prerequisites
- Python 3.8+
- pip

# Installation

git clone https://github.com/<your-username>/tastytrove.git
pip install -r requirements.txt

# Run the App

python app.py

The app will be available at http://127.0.0.1:5000/.
