import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import tiktoken
import base64
import re
from openai import OpenAI, AsyncOpenAI
from config import openai_api_conf as conf
from pages.rate_controller import RateController
from typing import Tuple, Iterable, AsyncIterable, List, Dict, Any, Optional

client = None
async_client = None

if conf.OPENAI_API_BASE:
    client = OpenAI(api_key=conf.OPENAI_API_KEY, base_url=conf.OPENAI_API_BASE)
    async_client = AsyncOpenAI(api_key=conf.OPENAI_API_KEY, base_url=conf.OPENAI_API_BASE)
else:
    client = OpenAI(api_key=conf.OPENAI_API_KEY)
    async_client = AsyncOpenAI(api_key=conf.OPENAI_API_KEY)

rate_control = RateController(
    limit=conf.N_LIMIT,
    period_sec=conf.PERIOD_SEC,
    backoff_max_retry=conf.BACKOFF_MAX_RETRY,
    backoff_on_errors=(
        Exception,  # Using general exception instead of specific OpenAI error types
    )
)


# wrap the api to apply rate control and retry logics
@rate_control.apply(asynchronous=False)
def chat_completion_create(*args, **kwargs):
    return client.chat.completions.create(*args, **kwargs)


@rate_control.apply(asynchronous=True)
async def chat_completion_acreate(*args, **kwargs):
    return await async_client.chat.completions.create(*args, **kwargs)


class OpenaiAPIChat:
    """
    A class for making conversation with Openai style REST api easier.
    It keeps chat history, takes care of streaming response,
    rate control and retry logics, with asynchronous support.
    """

    def __init__(
            self,
            model_name: str = conf.DEFAULT_MODEL_NAME,
            system_prompt: str = conf.DEFAULT_SYS_PROMPT,
            max_retry: int = 10,
            image_path: Optional[str] = None
    ):
        """
         Initialize the chat instance.
        :param model_name: The name of the model to be used.
        :param system_prompt: The system prompt to be used.
        :param max_retry: The maximum number of retry attempts for API calls.
        :param image_path: Optional path to a folder containing images for translation enhancement.
        """
        self.model_name = model_name
        self.chat_log = []
        self.sys_prompt = system_prompt
        self.encoding = tiktoken.get_encoding(conf.ENC_MAP.get(model_name, 'cl100k_base'))
        self.image_path = image_path  # Add image_path attribute

        self.max_retry = max_retry
        self.retry_cnt = 0

    def _get_image_files(self) -> List[str]:
        """Get image files from the image_path directory.
        
        :return: List of file paths to images
        """
        if not self.image_path or not os.path.exists(self.image_path) or not os.path.isdir(self.image_path):
            return []
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        image_files = []
        
        for filename in os.listdir(self.image_path):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                file_path = os.path.join(self.image_path, filename)
                if os.path.isfile(file_path):
                    image_files.append(file_path)

        print(f"Found {len(image_files)} image(s) in {self.image_path}")
        print(f"Image files: {image_files}")
        
        return image_files
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64.
        
        :param image_path: Path to the image file
        :return: Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _create_message_with_images(self, user_prompt: str) -> List[Dict[str, Any]]:
        """Create message with images for the API call.
        
        :param user_prompt: The text prompt from the user
        :return: List of message content objects including text and images
        """
        image_files = self._get_image_files()

        # If no images, send simple text
        if not image_files:
            return [{'role': 'user', 'content': user_prompt}]

        # Embed images as markdown in the message content
        import mimetypes
        content_str = user_prompt + "\n\n"
        for image_path in image_files:
            try:
                base64_image = self._encode_image(image_path)
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type:
                    mime_type = 'application/octet-stream'
                filename = os.path.basename(image_path)
                # Use markdown image syntax with base64 data URI
                content_str += f"![{filename}](data:{mime_type};base64,{base64_image})\n"
                print(f"Embedded image in markdown: {filename}")
            except Exception as e:
                print(f"Failed to encode image {image_path}: {e}")
        return [{'role': 'user', 'content': content_str}]

    def _make_msg(self, user_prompt, to_continue=False):
        """Create message for API call, including images if available."""
        msg = [
            {
                'role': 'system',
                'content': self.sys_prompt
            },
            *self.chat_log
        ]
        
        if not to_continue:
            # If we have images available, create a message with images
            if self.image_path:
                msg.extend(self._create_message_with_images(user_prompt))
            else:
                # Standard text message
                msg.append({
                    'role': 'user',
                    'content': user_prompt
                })
        return msg

    def clear(self):
        """Clear chat history"""
        self.chat_log = []

    def get_response(
            self,
            user_prompt: str,
            to_continue: bool = False,
            **extra_kwargs
    ) -> tuple[str, str]:
        """
        Get a response from the model synchronously.
        :param user_prompt: The user's input
        :param to_continue: Flag indicating if the conversation should continue
        :param extra_kwargs: Additional keyword arguments for API call
        :return: A tuple containing the response content and finish reason
        """
        retry_cnt = 0
        while retry_cnt < self.max_retry:
            try:
                response = chat_completion_create(
                    model=self.model_name,
                    messages=self._make_msg(user_prompt, to_continue),
                    stream=False,
                    **extra_kwargs
                )
                full_content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                
                # For chat history simplicity, store only text even if images were used
                self.chat_log += OpenaiAPIChat.round_format(user_prompt, full_content)
                return full_content, finish_reason
            except Exception as error:
                retry_cnt += 1
                print(error, f'retry: {retry_cnt} / {self.max_retry}')
            print('max retry reached')
            return '', ''

    async def get_aresponse(
            self,
            user_prompt: str,
            to_continue: bool = False,
            **extra_kwargs
    ) -> tuple[str, str]:
        """
        Get a response from the model asynchronously.
        :param user_prompt: The user's input
        :param to_continue: Flag indicating if the conversation should continue
        :param extra_kwargs: Additional keyword arguments for API call
        :return: A tuple containing the response content and finish reason
        """
        retry_cnt = 0
        while retry_cnt < self.max_retry:
            try:
                response = await chat_completion_acreate(
                    model=self.model_name,
                    messages=self._make_msg(user_prompt, to_continue),
                    stream=False,
                    **extra_kwargs
                )
                full_content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                
                # For chat history simplicity, store only text even if images were used
                self.chat_log += OpenaiAPIChat.round_format(user_prompt, full_content)
                return full_content, finish_reason

            except Exception as error:
                retry_cnt += 1
                print(error, f'retry: {retry_cnt} / {self.max_retry}')
            print('max retry reached')
            return '', ''

    def get_stream_response(
            self,
            user_prompt: str,
            to_continue: bool = False,
            **extra_kwargs
    ) -> Iterable[Tuple[str, str]]:
        """
        Get streaming response from the model synchronously.
        :param user_prompt: The user's input
        :param to_continue: Flag indicating if the conversation should continue
        :param extra_kwargs: Additional keyword arguments for API call
        :return Generator yields a tuple of content shreds and stop reason
        """
        response = chat_completion_create(
            model=self.model_name,
            messages=self._make_msg(user_prompt, to_continue),
            stream=True,
            **extra_kwargs
        )
        role = None
        full_content = ''
        for chunk in response:
            delta = chunk.choices[0].delta
            role = getattr(delta, 'role', role)
            content = getattr(delta, 'content', '') or ''
            full_content += content
            finish_reason = chunk.choices[0].finish_reason
            yield content, finish_reason
        
        # For chat history simplicity, store only text even if images were used
        self.chat_log.append({'role': 'user', 'content': user_prompt})
        self.chat_log.append({'role': role or 'assistant', 'content': full_content})

    async def get_stream_aresponse(
            self,
            user_prompt: str,
            to_continue: bool = False,
            **extra_kwargs
    ) -> AsyncIterable[Tuple[str, str]]:
        """
        Get streaming response from the model asynchronously.
        :param user_prompt: The user's input
        :param to_continue: Flag indicating if the conversation should continue
        :param extra_kwargs: Additional keyword arguments for API call
        :return AsyncGenerator yields a tuple of content shreds and stop reason
        """
        response = await chat_completion_acreate(
            model=self.model_name,
            messages=self._make_msg(user_prompt, to_continue),
            stream=True,
            **extra_kwargs
        )
        role = None
        full_content = ''
        async for chunk in response:
            delta = chunk.choices[0].delta
            role = getattr(delta, 'role', role)
            content = getattr(delta, 'content', '') or ''
            full_content += content
            finish_reason = chunk.choices[0].finish_reason
            yield content, finish_reason
        
        # For chat history simplicity, store only text even if images were used
        self.chat_log.append({'role': 'user', 'content': user_prompt})
        self.chat_log.append({'role': role or 'assistant', 'content': full_content})

    def n_tokens(self, text):
        """
        Calculate the number of tokens for the model in a given text.
        :param text: The text to calculate token count.
        :return: Number of tokens
        """
        return len(self.encoding.encode(text))

    @staticmethod
    def round_format(user, assistant):
        return [
            {'role': 'user', 'content': user},
            {'role': 'assistant', 'content': assistant}
        ]


async def translate_text_entry(
        text: str, 
        source_lang: str, 
        target_lang: str, 
        mapping_table: dict, 
        software_type: str, 
        image_path: Optional[str] = None,
        model_name: str = None,
        is_batch: bool = False,
        preserve_newlines: bool = True
    ) -> str:
    """
    Translate a single text entry or a batch of text entries using the translation model.
    
    :param text: Text to translate or JSON string for batch translation
    :param source_lang: Source language
    :param target_lang: Target language
    :param mapping_table: Dictionary with specific name translations
    :param software_type: Type of software being translated
    :param image_path: Optional path to images for translation enhancement
    :param model_name: Optional model name override
    :param is_batch: Whether the input is a batch of text entries in JSON format
    :param preserve_newlines: Whether to explicitly preserve newlines in the translation
    :return: Translated text or JSON string for batch translation
    """
    if not text or str(text).strip() == '':
        return ''
    
    # Get the model name from config if not specified
    if not model_name and hasattr(conf, 'TRANSLATE_MODEL'):
        from config import translate_config
        model_name = translate_config.TRANSLATE_MODEL
    
    # Initialize the chat with appropriate system prompt
    from prompts.translate_prompts import translate_sys_prompt, translate_prompt
    chat = OpenaiAPIChat(
        model_name=model_name or conf.DEFAULT_MODEL_NAME,
        system_prompt=translate_sys_prompt(source_lang, target_lang, software_type),
        image_path=image_path
    )
    
    # Check if any specific names apply to this text
    relevant_specific_names = {}
    if mapping_table:
        if is_batch:
            # For batch translation, check all text entries
            all_text = text  # text is already the JSON string
            for source_term, target_term in mapping_table.items():
                if source_term in all_text:
                    relevant_specific_names[source_term] = target_term
        else:
            # For single text translation
            for source_term, target_term in mapping_table.items():
                if source_term in text:
                    relevant_specific_names[source_term] = target_term

    response = ''
    # try:
    prompt = translate_prompt(
        text,
        source_lang,
        target_lang,
        software_type,
        relevant_specific_names,
    )

    
    # Get translation
    async for chunk, stop_reason in chat.get_stream_aresponse(prompt, temperature=0.01):
        response += chunk
        
    # For batch translations (JSON), we return the raw response to be parsed by the caller
    if is_batch:
        return response
        
    # Clean up the response for single text translation
    response = response.strip('"\'')
    if "```" in response:
        # If the model wraps the translation in code blocks, extract just the translation
        match = re.search(r"```(?:\w*\n)?(.*?)```", response, re.DOTALL)
        if match:
            response = match.group(1).strip()
    # except Exception as e:
    #     print(f"Error translating text: {e}")
    #     return f"ERROR: {str(e)[:100]}" 
        
    return response
