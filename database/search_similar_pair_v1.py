"""
This script searches for similar text pairs in a JSON database based on grammar, term similarity, 
and communicative intent. It returns the top matches for a given source text.
"""

import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from collections import Counter
import re
import nltk
import string
import sys
from sklearn.feature_extraction.text import TfidfVectorizer

# Download necessary NLTK resources if not already downloaded
try:
    nltk.data.find('corpora/stopwords')
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
    # Check for punkt_tab resource that's needed by the sentence tokenizer
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("Downloading additional required NLTK resources...")
        nltk.download('punkt_tab')
except LookupError:
    nltk.download('stopwords')
    nltk.download('punkt') 
    nltk.download('punkt_tab')  # Download punkt_tab as well
    nltk.download('averaged_perceptron_tagger')

from nltk.corpus import stopwords
from nltk import pos_tag, word_tokenize
from nltk.tokenize import sent_tokenize

# We'll use NLTK only for NLP processing
print("Using NLTK for NLP processing")
spacy_available = False
nlp = None

class SimilarPairSearcher:
    def __init__(self, json_path):
        """
        Initialize the searcher with a JSON database.
        
        Args:
            json_path (str): Path to the JSON file containing translation pairs
        """
        self.json_path = json_path
        self.data = self._load_json_data()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.english_texts = [pair[0] for pair in self.data.values()]
        self.stop_words = set(stopwords.words('english'))
        
        # Generate embeddings for grammar-based similarity
        self.embeddings = self._create_embeddings()
        self.index = self._create_faiss_index()
        
        # Create TF-IDF vectorizer for term-based similarity
        self.tfidf_vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),  # Use both single words and bigrams
            stop_words='english',
            max_features=5000
        )
        # Fit vectorizer on the English texts
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.english_texts)
        
        # Define intent patterns (for recommendation, import, etc.)
        self.intent_patterns = {
            'recommendation': [r'recommend', r'suggest', r'advice', r'should', r'better', r'best'],
            'instruction': [r'how to', r'steps to', r'guide', r'instruction', r'follow'],
            'warning': [r'warning', r'caution', r'beware', r'careful', r'danger', r'alert'],
            'import': [r'import', r'upload', r'input', r'insert', r'load'],
            'export': [r'export', r'download', r'save', r'output'],
            'query': [r'\?', r'how', r'what', r'when', r'where', r'who', r'which', r'why'],
            'notification': [r'notif', r'alert', r'inform', r'selected', r'complete', r'done']
        }
        
    def _load_json_data(self):
        """Load the JSON data from the file."""
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"JSON file not found at {self.json_path}")
            
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert from dictionary of lists to dictionary of tuples if needed
        return {int(k): (v[0], v[1]) if isinstance(v, list) else v for k, v in data.items()}
    
    def _create_embeddings(self):
        """Create embeddings for all English texts."""
        return self.model.encode(self.english_texts)
    
    def _create_faiss_index(self):
        """Create a FAISS index for fast similarity search."""
        dimension = self.embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(self.embeddings.astype(np.float32))
        return index    
    def extract_terms(self, text):
        """
        Extract significant terms from a text, removing stopwords and applying simple normalization.
        
        Args:
            text (str): The text to extract terms from
            
        Returns:
            list: A list of significant terms from the text
        """
        tokens = []
        # Use NLTK for tokenization
        try:
            # Use word_tokenize for better tokenization
            raw_tokens = word_tokenize(text.lower())
            
            # Filter out stopwords and punctuation
            for word in raw_tokens:
                # Remove punctuation
                word = ''.join(c for c in word if c.isalnum())
                if word and len(word) > 1 and word not in self.stop_words:
                    tokens.append(word)
        except Exception as e:
            print(f"Warning: Error in tokenization, using simple split: {e}")
            # Fallback to simpler tokenization
            for word in text.lower().split():
                # Remove punctuation
                word = ''.join(c for c in word if c.isalnum())
                if word and len(word) > 1 and word not in self.stop_words:
                    tokens.append(word)
        
        return tokens
    def extract_grammatical_structure(self, text):
        """
        Extract grammatical structure information from text.
        
        Args:
            text (str): The text to analyze
            
        Returns:
            list: A list of POS tags representing the grammatical structure
        """
        try:
            # Use NLTK POS tagging
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            return [tag for _, tag in pos_tags]
        except LookupError:
            # If there's an issue with NLTK resources, use a simpler approach
            # print("Warning: NLTK resources not available. Using simple tokenization.")
            # Simple fallback: just split by spaces and assume nouns
            tokens = text.split()
            return ['NOUN'] * len(tokens)
        except Exception as e:
            print(f"Warning: Error in POS tagging, using simple fallback: {e}")
            words = text.split()
            return ['NOUN'] * len(words)
    
    def detect_intent(self, text):
        """
        Detect the communicative intent of the text.
        
        Args:
            text (str): The text to analyze
            
        Returns:
            dict: Detected intents with confidence scores
        """
        text = text.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                score += len(matches) * 0.2  # Each match increases score
            
            intent_scores[intent] = min(score, 1.0)  # Cap at 1.0
            
        return intent_scores
    
    def search_grammar_similarity(self, query, top_n=10):
        """
        Search for sentences with similar grammar structure.
        
        Args:
            query (str): The English text to search for
            top_n (int): Number of top results to return
            
        Returns:
            list: Top matches with their indices and similarity scores
        """
        # First, check for exact matches
        exact_match_results = []
        query_lower = query.lower().strip()
        for idx, (key, (eng_text, trans_text)) in enumerate(self.data.items()):
            if eng_text.lower().strip() == query_lower:
                exact_match_results.append({
                    'index': key,
                    'english': eng_text,
                    'translation': trans_text,
                    'similarity': 1.0,
                    'match_type': 'exact'
                })
        
        # If exact matches found, return them
        if exact_match_results:
            print(f"Found exact match: {len(exact_match_results)} results")
            return exact_match_results
        
        # Get grammatical structure of query for more precise matching
        query_pos_tags = self.extract_grammatical_structure(query)
        
        # Use sentence transformers for semantic search
        query_embedding = self.model.encode([query])[0].reshape(1, -1).astype(np.float32)
        distances, indices = self.index.search(query_embedding, min(top_n * 2, len(self.english_texts)))
        
        # Map indices to original data keys
        keys_list = list(self.data.keys())
        
        # Collect results with grammatical structure similarity boost
        results = []
        for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            # Check if index is valid
            if 0 <= idx < len(keys_list):
                original_idx = keys_list[idx]
                english_text = self.data[original_idx][0]
                
                # Calculate base similarity from sentence embeddings (higher is better)
                base_similarity = 1 / (1 + distance)
                
                # Get grammatical structure of database entry
                entry_pos_tags = self.extract_grammatical_structure(english_text)
                
                # Calculate similarity of grammatical structures
                # Compare POS tags sequences
                pos_sim = 0
                min_len = min(len(query_pos_tags), len(entry_pos_tags))
                if min_len > 0:
                    matching_tags = sum(1 for i in range(min_len) 
                                       if i < len(query_pos_tags) and i < len(entry_pos_tags) 
                                       and query_pos_tags[i] == entry_pos_tags[i])
                    pos_sim = matching_tags / min_len
                
                # Combine base similarity with grammatical structure similarity
                # Weight: 70% semantic similarity, 30% grammatical structure
                final_similarity = (0.7 * base_similarity) + (0.3 * pos_sim)
                
                results.append({
                    'index': original_idx,
                    'english': english_text,
                    'translation': self.data[original_idx][1],
                    'similarity': float(final_similarity),
                    'match_type': 'grammar'
                })
        
        # Sort by similarity score
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_n]
    
    def search_term_similarity(self, query, top_n=10):
        """
        Search for sentences with similar terms.
        
        Args:
            query (str): The English text to search for
            top_n (int): Number of top results to return
            
        Returns:
            list: Top matches with their indices and similarity scores
        """
        # Extract significant terms from query
        query_terms = self.extract_terms(query)
        
        # Use TF-IDF for term-based matching
        query_vec = self.tfidf_vectorizer.transform([query])
        
        # Compute cosine similarity between query and all database entries
        from sklearn.metrics.pairwise import cosine_similarity
        cosine_similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Create index-similarity pairs and sort by similarity (descending)
        similarity_pairs = list(enumerate(cosine_similarities))
        similarity_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Map to original indices and create result objects
        keys_list = list(self.data.keys())
        results = []
        for idx, similarity in similarity_pairs[:top_n]:
            if 0 <= idx < len(keys_list):
                original_idx = keys_list[idx]
                english_text = self.data[original_idx][0]
                
                # Additional term overlap check
                entry_terms = self.extract_terms(english_text)
                
                # Count matching terms (including lemmatized forms)
                query_terms_set = set(query_terms)
                entry_terms_set = set(entry_terms)
                term_overlap = len(query_terms_set.intersection(entry_terms_set))
                
                # Calculate Jaccard similarity
                union_size = len(query_terms_set.union(entry_terms_set))
                jaccard_sim = term_overlap / union_size if union_size > 0 else 0
                
                # Combine TF-IDF similarity with Jaccard similarity
                # Weight: 60% TF-IDF, 40% Jaccard
                final_similarity = (0.6 * float(similarity)) + (0.4 * jaccard_sim)
                
                results.append({
                    'index': original_idx,
                    'english': english_text,
                    'translation': self.data[original_idx][1],
                    'similarity': float(final_similarity),
                    'match_type': 'term',
                    'matching_terms': term_overlap
                })
        
        return results
    
    def search_intent_similarity(self, query, top_n=10):
        """
        Search for sentences with similar communicative intent.
        
        Args:
            query (str): The English text to search for
            top_n (int): Number of top results to return
            
        Returns:
            list: Top matches with their indices and similarity scores
        """
        # Analyze intent of query
        query_intent = self.detect_intent(query)
        
        # Find entries with similar intent
        intent_similarities = []
        for idx, entry_key in enumerate(self.data.keys()):
            english_text = self.data[entry_key][0]
            entry_intent = self.detect_intent(english_text)
            
            # Calculate cosine similarity between intent vectors
            query_vec = np.array([query_intent.get(intent, 0) for intent in self.intent_patterns.keys()])
            entry_vec = np.array([entry_intent.get(intent, 0) for intent in self.intent_patterns.keys()])
            
            # Avoid division by zero
            query_norm = np.linalg.norm(query_vec)
            entry_norm = np.linalg.norm(entry_vec)
            
            if query_norm > 0 and entry_norm > 0:
                similarity = np.dot(query_vec, entry_vec) / (query_norm * entry_norm)
            else:
                similarity = 0
            
            intent_similarities.append((entry_key, similarity))
        
        # Sort by intent similarity (descending) and get top_n
        top_results = sorted(intent_similarities, key=lambda x: x[1], reverse=True)[:top_n]
        
        results = []
        for original_idx, similarity in top_results:
            if similarity > 0:  # Only include if there's some intent similarity
                results.append({
                    'index': original_idx,
                    'english': self.data[original_idx][0],
                    'translation': self.data[original_idx][1],
                    'similarity': float(similarity),
                    'match_type': 'intent'
                })
                
        return results
    
    def search(self, query, grammar_top_n=10, term_top_n=10, intent_top_n=5, min_score=0.5):
        """
        Search for similar pairs based on grammar, term similarity, and communicative intent.
        
        Args:
            query (str): The English text to search for
            grammar_top_n (int): Number of top grammar similarity results
            term_top_n (int): Number of top term similarity results
            intent_top_n (int): Number of top intent similarity results
            min_score (float): Minimum similarity score threshold (0.0 to 1.0)
            
        Returns:
            dict: {'query': query, 'grammar_similarity': [...], 'term_similarity': [...], 'intent_similarity': [...]}
        """
        print(f"Search query: '{query}'")
        
        # Get grammar similarity results
        grammar_results = self.search_grammar_similarity(query, grammar_top_n * 2)
        exact_matches = [r for r in grammar_results if r['similarity'] >= 0.999]
        
        # If exact matches found, prioritize them
        if exact_matches:
            print(f"Found {len(exact_matches)} exact matches")
            grammar_results = exact_matches
        else:
            # Filter by minimum score
            print(f"No exact matches found, filtering by similarity threshold: {min_score}")
            grammar_results = [r for r in grammar_results if r['similarity'] >= min_score]
            
            if grammar_results:
                top_similarity = max([r['similarity'] for r in grammar_results])
                print(f"Found {len(grammar_results)} grammar-similar results, highest similarity: {top_similarity:.4f}")
            else:
                print(f"No results with similarity >= {min_score} found")
        
        # Limit to requested number
        grammar_results = grammar_results[:grammar_top_n]
        
        # Get term similarity results
        term_results = self.search_term_similarity(query, term_top_n * 2)
        term_results = [r for r in term_results if r['similarity'] >= min_score]
        term_results = term_results[:term_top_n]
        
        if term_results:
            print(f"Found {len(term_results)} term-similar results")
        
        # Get intent similarity results
        intent_results = self.search_intent_similarity(query, intent_top_n * 2)
        intent_results = [r for r in intent_results if r['similarity'] >= min_score]
        intent_results = intent_results[:intent_top_n]
        
        if intent_results:
            print(f"Found {len(intent_results)} intent-similar results")
        
        return {
            'query': query,
            'grammar_similarity': grammar_results,
            'term_similarity': term_results,
            'intent_similarity': intent_results
        }

def search_similar_pair(source_text, json_path=None, grammar_top_n=10, term_top_n=10, intent_top_n=5, min_score=0.5):
    """
    Search for similar pairs in the database.
    
    Args:
        source_text (str): The source text to search for
        json_path (str, optional): Path to the JSON database
        grammar_top_n (int): Number of grammar similarity results
        term_top_n (int): Number of term similarity results
        intent_top_n (int): Number of intent similarity results
        min_score (float): Minimum similarity score threshold (0.0 to 1.0)
        
    Returns:
        dict: Search results
    """
    if json_path is None:
        # Use default path
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "Report", "Database", "enu_cht_mapping.json"
        )
    
    searcher = SimilarPairSearcher(json_path)
    return searcher.search(source_text, grammar_top_n, term_top_n, intent_top_n, min_score)

def format_results(results, output):
    """Format the results for display."""
    if results['grammar_similarity']:
        for i, item in enumerate(results['grammar_similarity'], 1):
            inform = ('grammar', item['english'], item['translation'], round(item['similarity'], 4))
            if inform not in output:
                output.append(inform)
    else:
        output.append("No grammar matches with score ≥ 0.5 were found.")

    if results['term_similarity']:
        for i, item in enumerate(results['term_similarity'], 1):
            inform = ('terms', item['english'], item['translation'], round(item['similarity'], 4))
            if inform not in output:
                output.append(inform)
    else:
        print("No term matches with score ≥ 0.5 were found.")
        
    if results['intent_similarity']:
        for i, item in enumerate(results['intent_similarity'], 1):
            inform = ('intent', item['english'], item['translation'], round(item['similarity'], 4))
            if inform not in output:
                output.append(inform)
    else:
        print("No intent matches with score ≥ 0.5 were found.")
    
    return output

def main(translate_dict, database_path, grammar_top_n=10, term_top_n=10, intent_top_n=5, min_score=0.5):
    """
    Main function to search for similar pairs for multiple source texts.
    
    Args:
        translate_dict (dict): Dictionary of texts to translate (keys are indices, values are texts)
        database_path (str): Path to the translation database JSON file
        grammar_top_n (int): Number of grammar similarity results to return
        term_top_n (int): Number of term similarity results to return
        intent_top_n (int): Number of intent similarity results to return
        min_score (float): Minimum similarity score threshold (0.0 to 1.0)
        
    Returns:
        list: Formatted output of search results
    """
    output = []
    for index, value in translate_dict.items():
        source_text = value
        print(f"Searching for similar pairs to: '{source_text}'")
        print(f"Using database: {database_path}")
        print("This may take a moment as the embeddings are being generated...\n")
        
        # Run the search
        results = search_similar_pair(
            source_text=source_text,
            json_path=database_path,
            grammar_top_n=grammar_top_n,
            term_top_n=term_top_n,
            intent_top_n=intent_top_n,
            min_score=min_score
        )
    
        # Print formatted results
        output = format_results(results, output)
        # print("====================================")
        # print(f"Get similar pairs for '{source_text}'")
        # print(f"output: {output}")
        # print("====================================")

    return output

if __name__ == "__main__":
    # Example usage
    source_text = 'Your generated videos will be stored on the cloud server for 30 days. We recommend downloading the ones you&apos;d like to keep to your local storage.'
    main({'0': source_text},
         r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v10\database\PDR_enu_ita_database.json")
