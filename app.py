import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from ml_models import MLModels

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tastytrove_secret_key_1234'
db_url = os.environ.get('DATABASE_URL', 'sqlite:///database1.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

db = SQLAlchemy(app)

# Initialize ML Models
ml_model = MLModels()

# Recipe DB Model
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    time = db.Column(db.Integer, nullable=False, default=15)
    rating = db.Column(db.Float, nullable=False, default=4.0)
    rating_count = db.Column(db.Integer, nullable=False, default=1)
    rating_sum = db.Column(db.Float, nullable=False, default=4.0)
    description = db.Column(db.Text, nullable=True)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    author = db.Column(db.String(100), nullable=True, default="TastyTrove Chef")
    video_url_ml = db.Column(db.String(500), nullable=True)
    video_url_en = db.Column(db.String(500), nullable=True)
    likes = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "time": self.time,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "rating_sum": self.rating_sum,
            "description": self.description,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "category": self.category,
            "image_url": self.image_url,
            "author": self.author,
            "video_url_ml": self.video_url_ml,
            "video_url_en": self.video_url_en,
            "likes": self.likes
        }

def seed_database():
    """Seed the database with pre-parsed recipe data on first run."""
    if Recipe.query.count() == 0:
        seed_file = os.path.join(app.root_path, 'seed_recipes.json')
        if os.path.exists(seed_file):
            with open(seed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    recipe = Recipe(
                        title=item['title'],
                        time=item['time'],
                        rating=item['rating'],
                        rating_count=item['rating_count'],
                        rating_sum=item['rating_sum'],
                        description=item['description'],
                        ingredients=item['ingredients'],
                        instructions=item['instructions'],
                        category=item['category'],
                        image_url=item['image_url'],
                        author=item['author'],
                        video_url_ml=item['video_url_ml'],
                        video_url_en=item['video_url_en'],
                        likes=item['likes']
                    )
                    db.session.add(recipe)
                db.session.commit()
            print("Database successfully seeded with default recipes.")
        else:
            print(f"Warning: Seed file not found at {seed_file}")

def train_ml():
    """Train the TF-IDF recommender and Naive Bayes category classifier."""
    recipes = Recipe.query.all()
    recipes_list = [r.to_dict() for r in recipes]
    ml_model.train_recommender(recipes_list)
    ml_model.train_category_predictor(recipes_list)
    print("Machine Learning models successfully trained/updated.")

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/recipes')
def recipes_page():
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    
    query = Recipe.query
    if category_filter:
        query = query.filter(Recipe.category == category_filter)
    if search_query:
        query = query.filter(Recipe.title.ilike(f'%{search_query}%'))
        
    recipes = query.all()
    return render_template('recipe.html', recipes=recipes, search_query=search_query, category_filter=category_filter)

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Compute content-based AI recommendations
    rec_ids = ml_model.get_recommendations(recipe_id, limit=3)
    recommendations = []
    if rec_ids:
        recommendations = Recipe.query.filter(Recipe.id.in_(rec_ids)).all()
        
        # Sort recommendations to match similarity rank order
        recommendations_map = {r.id: r for r in recommendations}
        recommendations = [recommendations_map[rid] for rid in rec_ids if rid in recommendations_map]
    
    # Parse ingredients and instructions split by newlines for clean display
    ingredients_list = [line.strip() for line in recipe.ingredients.split('\n') if line.strip()]
    instructions_list = [line.strip() for line in recipe.instructions.split('\n') if line.strip()]
    
    return render_template('recipe_detail.html', 
                           recipe=recipe, 
                           recommendations=recommendations,
                           ingredients=ingredients_list,
                           instructions=instructions_list)

@app.route('/recipe/<int:recipe_id>/rate', methods=['POST'])
def rate_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    try:
        data = request.get_json() or {}
        val = float(data.get('rating', 0))
        if 1 <= val <= 5:
            recipe.rating_count += 1
            recipe.rating_sum += val
            recipe.rating = round(recipe.rating_sum / recipe.rating_count, 1)
            db.session.commit()
            
            # Retrain ML models dynamically to incorporate new rating profile
            train_ml()
            
            return jsonify({
                "success": True,
                "rating": recipe.rating,
                "rating_count": recipe.rating_count
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    return jsonify({"success": False, "error": "Invalid rating input"}), 400

@app.route('/submit', methods=['GET', 'POST'])
def submit_recipe():
    if request.method == 'POST':
        title = request.form.get('recipeName', '').strip()
        author = request.form.get('author', '').strip() or 'Anonymous'
        category = request.form.get('category', '').strip()
        ingredients = request.form.get('ingredients', '').strip()
        instructions = request.form.get('instructions', '').strip()
        time_str = request.form.get('time', '').strip()
        
        try:
            time = int(time_str) if time_str else 15
        except ValueError:
            time = 15
            
        # File upload handling
        image_file = request.files.get('image')
        image_url = 'https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=1000'
        if image_file and image_file.filename:
            from werkzeug.utils import secure_filename
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            image_url = f'/static/uploads/{filename}'
            
        if not title or not ingredients or not instructions or not category:
            flash("Please fill out all required fields.", "error")
            return redirect(url_for('submit_recipe'))
            
        new_recipe = Recipe(
            title=title,
            author=author,
            category=category,
            ingredients=ingredients,
            instructions=instructions,
            time=time,
            image_url=image_url,
            rating=5.0,
            rating_count=1,
            rating_sum=5.0,
            likes=0
        )
        db.session.add(new_recipe)
        db.session.commit()
        
        # Retrain ML models dynamically to make new recipe searchable and recommendable
        train_ml()
        
        flash("Recipe submitted successfully!", "success")
        return redirect(url_for('recipes_page'))
        
    return render_template('submit.html')

@app.route('/api/predict-category', methods=['POST'])
def predict_category_api():
    try:
        data = request.get_json() or {}
        ingredients = data.get('ingredients', '').strip()
        if not ingredients:
            return jsonify({"category": "Breakfast"})
            
        predicted = ml_model.predict_category(ingredients)
        return jsonify({"category": predicted})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/about')
def about():
    return render_template('about.html')

def load_ml_model():
    """Load pre-trained Naive Bayes category predictor model weights from JSON."""
    model_path = os.path.join(app.root_path, 'category_model.json')
    if os.path.exists(model_path):
        try:
            with open(model_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
                ml_model.categories = model_data.get('categories', ml_model.categories)
                ml_model.category_priors = model_data.get('category_priors', {})
                
                wcp = model_data.get('word_cond_probs', {})
                from collections import defaultdict
                ml_model.word_cond_probs = defaultdict(dict, wcp)
                
                ml_model.vocab_nb = set(model_data.get('vocab_nb', []))
                
                from collections import Counter
                ml_model.category_total_words = Counter(model_data.get('category_total_words', {}))
                print("Successfully loaded AI Category Predictor weights from category_model.json")
        except Exception as e:
            print(f"Error loading category_model.json: {e}")
    else:
        print("Warning: category_model.json not found. Run train_model.py to generate it.")

# Initialize DB, seed data, train recommender, and load pre-trained weights
with app.app_context():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db.create_all()
    seed_database()
    train_ml()
    load_ml_model()

if __name__ == '__main__':
    app.run(debug=True)

