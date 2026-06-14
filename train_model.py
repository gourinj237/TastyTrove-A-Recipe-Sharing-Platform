import csv
import json
from ml_models import MLModels

def train():
    print("Loading dataset from recipe_dataset.csv...")
    dataset = []
    
    with open("recipe_dataset.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dataset.append({
                "title": row["title"],
                "category": row["category"],
                "ingredients": row["ingredients"]
            })
            
    print(f"Loaded {len(dataset)} training records.")
    
    # Initialize and train Naive Bayes Category Predictor
    ml = MLModels()
    print("Training Multinomial Naive Bayes model...")
    ml.train_category_predictor(dataset)
    
    # Package model weights
    model_data = {
        "categories": ml.categories,
        "category_priors": ml.category_priors,
        # Convert defaultdict to standard dict for JSON serialization
        "word_cond_probs": {cat: dict(probs) for cat, probs in ml.word_cond_probs.items()},
        "vocab_nb": list(ml.vocab_nb),
        "category_total_words": dict(ml.category_total_words)
    }
    
    # Save model weights to JSON
    output_file = "category_model.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(model_data, f, indent=4)
        
    print(f"Successfully trained and saved model weights to {output_file}!")

if __name__ == "__main__":
    train()
