import sys
import os
import base64
import mimetypes
from openai import OpenAI
from typing import List

# Add parent directory to path to import config and other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from config import openai_api_conf as conf
from prompts.refer_image_prompts import image_analysis_prompt
from pages.rate_controller import RateController

# Client setup
client = None
if conf.OPENAI_API_BASE:
    client = OpenAI(api_key=conf.OPENAI_API_KEY, base_url=conf.OPENAI_API_BASE)
else:
    client = OpenAI(api_key=conf.OPENAI_API_KEY)

# Rate controller setup from openai_api_chat.py
rate_control = RateController(
    limit=conf.N_LIMIT,
    period_sec=conf.PERIOD_SEC,
    backoff_max_retry=conf.BACKOFF_MAX_RETRY,
    backoff_on_errors=(
        Exception,
    )
)

# Wrapped API call from openai_api_chat.py
@rate_control.apply(asynchronous=False)
def chat_completion_create(*args, **kwargs):
    return client.chat.completions.create(*args, **kwargs)


class OpenaiAPIAnalysisImageChat:
    """
    A class for analyzing images with Openai style REST api.
    It mimics the structure of OpenaiAPIChat.
    """

    def __init__(
            self,
            model_name: str = "gpt-4o",
            max_tokens: int = 512,
            max_retry: int = 10
    ):
        """
         Initialize the chat instance.
        :param model_name: The name of the model to be used.
        :param max_tokens: The maximum number of tokens to generate.
        :param max_retry: The maximum number of retry attempts for API calls.
        """
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.max_retry = max_retry

    def get_describes_from_images(self, target_string: str, image_files: List[str]) -> str:
        """
        Get descriptions of images using OpenAI API.
        :param target_string: The target string for context.
        :param image_files: list of image file paths
        :return: descriptions of the images as a string
        """
        question = image_analysis_prompt(target_string)
        print(f"Question for OpenAI API: {question}")

        content = [{"type": "text", "text": question}]
        for file_path in image_files:
            try:
                with open(file_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
                mime, _ = mimetypes.guess_type(file_path)
                if not mime:
                    mime = 'application/octet-stream'

                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{base64_image}"}
                })
            except Exception as e:
                print(f"Error processing image file {file_path}: {e}")
                continue
        
        if len(content) == 1:
            print("No valid image files were processed.")
            return ""

        retry_cnt = 0
        while retry_cnt < self.max_retry:
            try:
                response = chat_completion_create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": content}],
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content
            except Exception as error:
                retry_cnt += 1
                print(f"An error occurred: {error}. Retry attempt {retry_cnt}")
                if retry_cnt >= self.max_retry:
                    print(f"Max retry reached. ERROR: {str(error)[:100]}")
                    return ""
        
        print("Error: Failed to get response from API after multiple retries.")
        return ""
