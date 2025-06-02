import os

# >>> openai api >>>
OPENAI_API_BASE = '' # please leave empty
OPENAI_API_KEY = "" # Please provide your own key
DEFAULT_MODEL_NAME = 'gpt-4-1106-preview'
DEFAULT_SYS_PROMPT = 'you are a helpful assistant.'

ENC_MAP = {
    'gpt-4-0613': 'cl100k_base',
    'gpt-4-1106-preview': 'cl100k_base',
    'gpt-3.5-turbo': 'cl100k_base',
    'text-embedding-ada-002': 'cl100k_base',
    'text-davinci-002': 'p50k_base',
    'text-davinci-003': 'p50k_base',
    'davinci': 'p50k_base'
}

# >>> api rate control >>>
N_LIMIT = 1
PERIOD_SEC = 6.0  # Increased from 3.5 to reduce streaming errors
BACKOFF_MAX_RETRY = 10
# <<< api rate control <<<
