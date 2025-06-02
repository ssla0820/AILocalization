"""
Example script to demonstrate the use of search_similar_pair.py
"""

import os
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from search_similar_pair import search_similar_pair, format_results

def main():
    # Example source text
    source_text = "0 images selected"
    
    # Get the path to the JSON database
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "Report", "Database", "enu_cht_mapping.json"
    )
    
    print(f"Searching for similar pairs to: '{source_text}'")
    print(f"Using database: {json_path}")
    print("This may take a moment as the embeddings are being generated...\n")
      # Run the search for top 10 grammar and top 10 term matches
    results = search_similar_pair(
        source_text=source_text,
        json_path=json_path,
        grammar_top_n=10,
        term_top_n=10,
        min_score=0.5  # Only include results with score >= 0.5
    )
    
    # Print formatted results
    print(format_results(results))

if __name__ == "__main__":
    main()
