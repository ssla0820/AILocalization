import os

# >>> gemini api >>>
GEMINI_API_KEY = ""  # Please provide your own key
# DEFAULT_MODEL_NAME = 'gemini-pro'  # Default text model
# GEMINI_VISION_MODEL = 'gemini-2.5-pro-preview-05-06'  # Model that supports image input
GEMINI_VISION_MODEL = 'gemini-2.0-flash'  # Model that supports image input
DEFAULT_SYS_PROMPT = 'you are a helpful assistant.'

# Model configuration
MODEL_CONFIG = {
    # 'gemini-pro': {
    #     'temperature': 0.0,  # Lower temperature for more deterministic responses
    #     'top_p': 1.0,  # Keep output diverse but controlled
    #     'top_k': 40,  # Limit token selection to top 40 for better quality
    #     'max_output_tokens': 4096,  # Maximum output length
    # },
    'gemini-2.5-pro-preview-05-06': {
        'temperature': 0.0,
        'top_p': 1.0,
        'top_k': 40,
        'max_output_tokens': 4096,
    },
    'gemini-2.0-flash': {
        'temperature': 0.0,
        'top_p': 1.0,
        'top_k': 40,
        'max_output_tokens': 4096,
    }
}

# >>> api rate control >>>
N_LIMIT = 1  # Number of requests allowed per period
PERIOD_SEC = 6.0  # Time period in seconds (increased from 3.5 to reduce streaming errors)
BACKOFF_MAX_RETRY = 10  # Maximum number of retries
# <<< api rate control <<<

# Safety settings (optional, comment out if not needed)
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]
