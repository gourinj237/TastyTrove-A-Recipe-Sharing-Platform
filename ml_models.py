import math
import re
from collections import Counter, defaultdict

def tokenize(text):
    """Tokenize text into lowercase alphanumeric words."""
    if not text:
        return []
    return re.findall(r'\b[a-z0-9]+\b', text.lower())

class MLModels:
    def __init__(self):
        # Recommendation engine data
        self.recipes = []
        self.vocab = set()
        self.idf = {}
        self.tfidf_vectors = {}  # recipe_id -> vector dict {word: tfidf_score}
        
        # Category predictor data (Naive Bayes)
        self.category_priors = {}
        self.word_cond_probs = defaultdict(dict)  # category -> word -> prob
        self.categories = ["Breakfast", "Snacks & Fast Foods", "Desserts", "Drinks"]
        self.vocab_nb = set()
        self.category_total_words = Counter()

    def train_recommender(self, recipes_list):
        """Train TF-IDF vectorizer and compute recipe similarity profiles.
        
        recipes_list should be a list of dictionaries with keys:
        'id', 'title', 'category', 'ingredients', 'description'
        """
        self.recipes = recipes_list
        self.vocab = set()
        doc_count = len(recipes_list)
        if doc_count == 0:
            return
            
        df = Counter()
        
        # Build document text representation
        doc_texts = {}
        for r in recipes_list:
            combined_text = " ".join([
                r.get('title', '') or '',
                r.get('category', '') or '',
                r.get('description', '') or '',
                r.get('ingredients', '') or ''
            ])
            tokens = tokenize(combined_text)
            doc_texts[r['id']] = tokens
            
            # Track document frequency for IDF
            unique_tokens = set(tokens)
            self.vocab.update(unique_tokens)
            for token in unique_tokens:
                df[token] += 1
                
        # Calculate IDF with smoothing
        self.idf = {}
        for token in self.vocab:
            self.idf[token] = math.log((1 + doc_count) / (1 + df[token])) + 1
            
        # Calculate TF-IDF vectors
        self.tfidf_vectors = {}
        for r in recipes_list:
            rid = r['id']
            tokens = doc_texts[rid]
            tf = Counter(tokens)
            vector = {}
            for token, count in tf.items():
                vector[token] = count * self.idf[token]
            self.tfidf_vectors[rid] = vector

    def get_recommendations(self, target_id, limit=3):
        """Find the top N most similar recipes to target_id using cosine similarity."""
        if target_id not in self.tfidf_vectors:
            return []
            
        target_vec = self.tfidf_vectors[target_id]
        target_norm = math.sqrt(sum(val**2 for val in target_vec.values()))
        if target_norm == 0:
            return []
            
        similarities = []
        for rid, vec in self.tfidf_vectors.items():
            if rid == target_id:
                continue
                
            # Dot product
            dot_product = sum(target_vec[w] * vec.get(w, 0) for w in target_vec)
            vec_norm = math.sqrt(sum(val**2 for val in vec.values()))
            
            if vec_norm == 0:
                similarity = 0
            else:
                similarity = dot_product / (target_norm * vec_norm)
                
            similarities.append((rid, similarity))
            
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [rid for rid, sim in similarities[:limit]]

    def train_category_predictor(self, recipes_list):
        """Train a Multinomial Naive Bayes classifier on recipe ingredients."""
        total_docs = len(recipes_list)
        if total_docs == 0:
            return
            
        category_counts = Counter()
        category_words = defaultdict(Counter)
        self.category_total_words = Counter()
        self.vocab_nb = set()
        
        for r in recipes_list:
            cat = r.get('category')
            if not cat or cat not in self.categories:
                continue
            category_counts[cat] += 1
            
            # Tokenize ingredients
            words = tokenize(r.get('ingredients', ''))
            for word in words:
                category_words[cat][word] += 1
                self.category_total_words[cat] += 1
                self.vocab_nb.add(word)
                
        # Calculate class prior probabilities P(C) with Laplace smoothing
        self.category_priors = {}
        for cat in self.categories:
            count = category_counts.get(cat, 0)
            self.category_priors[cat] = (count + 1) / (total_docs + len(self.categories))
            
        # Calculate word conditional probabilities P(W|C) with Laplace smoothing
        vocab_size = len(self.vocab_nb)
        self.word_cond_probs = defaultdict(dict)
        for cat in self.categories:
            total_word_count = self.category_total_words[cat]
            for word in self.vocab_nb:
                word_count = category_words[cat][word]
                self.word_cond_probs[cat][word] = (word_count + 1) / (total_word_count + vocab_size)

    def predict_category(self, ingredients_text):
        """Predict the category for a given ingredients list."""
        if not self.category_priors:
            return "Breakfast"
            
        words = tokenize(ingredients_text)
        best_cat = "Breakfast"
        best_score = float('-inf')
        
        vocab_size = len(self.vocab_nb)
        
        for cat in self.categories:
            # Start with log prior
            score = math.log(self.category_priors.get(cat, 0.25))
            total_word_count = self.category_total_words.get(cat, 0)
            
            # Sum log conditional probabilities of words
            for word in words:
                if word in self.vocab_nb:
                    score += math.log(self.word_cond_probs[cat][word])
                else:
                    # Smoothing for out-of-vocabulary words
                    score += math.log(1 / (total_word_count + vocab_size + 1))
                    
            if score > best_score:
                best_score = score
                best_cat = cat
                
        return best_cat
