import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import base64
import re
import asyncio
import google.generativeai as genai
from pages.rate_controller import RateController
from config import gemini_api_conf as conf
from typing import Tuple, Iterable, AsyncIterable, List, Dict, Any, Optional

# Configure the Gemini API
genai.configure(api_key=conf.GEMINI_API_KEY)

rate_control = RateController(
    limit=conf.N_LIMIT,
    period_sec=conf.PERIOD_SEC,
    backoff_max_retry=conf.BACKOFF_MAX_RETRY,
    backoff_on_errors=(Exception,)
)

# Wrap the API to apply rate control and retry logics
@rate_control.apply(asynchronous=False)
def chat_completion_create(*args, **kwargs):
    content = kwargs.pop('content', '')  # Remove content from kwargs
    temperature = kwargs.pop('temperature', 0.0)  # Remove temperature from kwargs
    seed = kwargs.pop('seed', None)  # Get seed parameter if provided
    
    # Create generation config
    generation_config = {
        'temperature': temperature,
        'top_p': 1.0,
        'top_k': 40,
        'max_output_tokens': 4096,
    }
    
    # Add seed to generation config if provided
    if seed is not None:
        generation_config['seed'] = seed
    
    # Configure safety settings if defined
    if hasattr(conf, 'SAFETY_SETTINGS'):
        kwargs['safety_settings'] = conf.SAFETY_SETTINGS
    
    # Always create a fresh model instance to avoid session closure issues
    model = genai.GenerativeModel(conf.GEMINI_VISION_MODEL)
    return model.generate_content(content, generation_config=generation_config, **kwargs)

@rate_control.apply(asynchronous=True)
async def chat_completion_acreate(*args, **kwargs):
    content = kwargs.pop('content', '')  # Remove content from kwargs
    temperature = kwargs.pop('temperature', 0.0)  # Get temperature parameter
    seed = kwargs.pop('seed', None)  # Get seed parameter if provided
    
    # Create generation config that will be used if the API supports it
    generation_config = {
        'temperature': temperature,
        'top_p': 1.0,
        'top_k': 40,
        'max_output_tokens': 4096,
    }
    
    # Add seed to generation config if provided, but only for synchronous API
    # Async API doesn't support seed in generation_config
    if seed is not None and False:  # Disabling seed for now since it's not supported
        generation_config['seed'] = seed
    
    # Configure safety settings if defined
    if hasattr(conf, 'SAFETY_SETTINGS'):
        kwargs['safety_settings'] = conf.SAFETY_SETTINGS
    
    # Always create a fresh model instance to avoid session closure issues
    model = genai.GenerativeModel(conf.GEMINI_VISION_MODEL)
    
    # Improved error handling - use existing event loop instead of creating new ones
    try:
        # First attempt with generation_config
        try:
            result = await model.generate_content_async(content, generation_config=generation_config, **kwargs)
            return result
        except Exception as config_error:
            print(f"Warning: Could not use generation_config with async API: {config_error}")
            # Fallback to standard call without generation parameters
            result = await model.generate_content_async(content, **kwargs)
            return result
    except Exception as e:
        print(f"Error in chat_completion_acreate: {e}")
        raise  # Re-raise the exception to be handled by the caller

class GeminiAPIChat:
    """
    A class for making conversation with Google Gemini API.
    It keeps chat history, takes care of streaming response,
    rate control and retry logics, with asynchronous support.
    """

    def __init__(
            self,
            model_name: str = conf.GEMINI_VISION_MODEL,
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
        self.image_path = image_path

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
    
    def _create_content_with_images(self, user_prompt: str) -> List[Dict[str, Any]]:
        """Create content with images for the API call.
        
        :param user_prompt: The text prompt from the user
        :return: List of content objects including text and images
        """
        content = [user_prompt]
        image_files = self._get_image_files()
        
        if not image_files:
            return content
        
        # Add images to content
        for image_path in image_files:
            try:
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                    content.append({
                        'type': 'image_url',
                        'image_url': {'url': f'data:image/jpeg;base64,{base64.b64encode(image_data).decode("utf-8")}'}
                    })
                    print(f"Added image: {os.path.basename(image_path)}")
            except Exception as e:
                print(f"Failed to load image {image_path}: {e}")
        
        return content    
    def _make_content(self, user_prompt, to_continue=False):
        """
        Create content for API call, including system prompt, chat history and user message
        """
        # For Gemini, we need to prepend the system prompt to the first user message
        if not self.chat_log:
            # First interaction, include system prompt
            if self.image_path:
                # With images
                content = self._create_content_with_images(f"{self.sys_prompt}\n\nUser: {user_prompt}")
            else:
                # Just text
                content = [f"{self.sys_prompt}\n\nUser: {user_prompt}"]
        else:
            # Subsequent interactions
            if not to_continue:
                if self.image_path:
                    # With images
                    content = self._create_content_with_images(user_prompt)
                else:
                    # Just text
                    content = [user_prompt]
            else:
                content = [user_prompt] if isinstance(user_prompt, str) else user_prompt
        
        return content


    def clear(self):
        """Clear chat history"""
        self.chat_log = []

    async def close(self):
        """Explicitly close resources used by this chat instance"""
        self.chat_log = []
        
        # Ensure all pending tasks are completed
        try:
            # Get the current loop
            try:
                loop = asyncio.get_running_loop()
                if not loop.is_closed():
                    # Just clear the tasks without attempting to create new ones
                    await asyncio.sleep(0.1)
                    
                    # We'll only cancel tasks that are part of the current loop
                    # and leave loop management to the caller
                    current_task = asyncio.current_task(loop)
                    pending_tasks = [task for task in asyncio.all_tasks(loop) 
                                    if not task.done() and task != current_task]
                    
                    # Cancel pending tasks if needed
                    if pending_tasks:
                        print(f"Cancelling {len(pending_tasks)} pending tasks...")
                        for task in pending_tasks:
                            task.cancel()
                        # Wait for cancellation to complete
                        try:
                            await asyncio.gather(*pending_tasks, return_exceptions=True)
                        except:
                            pass
            except RuntimeError:
                # No running loop to worry about
                pass
        except Exception as e:
            print(f"Error while closing chat resources: {e}")
            
        # Force garbage collection to help free resources
        import gc
        gc.collect()

    def get_response(
            self,
            user_prompt: str,
            to_continue: bool = False,
            temperature: float = 0.0,
            seed: int = None,
            **extra_kwargs
    ) -> tuple[str, str]:
        """
        Get a response from the model synchronously.
        :param user_prompt: The user's input
        :param to_continue: Flag indicating if the conversation should continue
        :param temperature: The temperature parameter for controlling randomness (0.0-1.0)
        :param seed: Optional seed for deterministic generation
        :param extra_kwargs: Additional keyword arguments for API call
        :return: A tuple containing the response content and finish reason
        """
        retry_cnt = 0
        while retry_cnt < self.max_retry:
            try:
                content = self._make_content(user_prompt, to_continue)
                
                # Add temperature and seed if provided
                if temperature is not None:
                    extra_kwargs['temperature'] = temperature
                if seed is not None:
                    extra_kwargs['seed'] = seed
                    
                response = chat_completion_create(content=content, **extra_kwargs)
                full_content = response.text
                finish_reason = "stop"  # Gemini doesn't provide finish reason
                
                # Store conversation for context
                self.chat_log.append({"role": "user", "parts": [user_prompt]})
                self.chat_log.append({"role": "model", "parts": [full_content]})
                
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
            temperature: float = 0.0,
            seed: int = None,
            **extra_kwargs
    ) -> tuple[str, str]:
        """
        Get a response from the model asynchronously.
        :param user_prompt: The user's input
        :param to_continue: Flag indicating if the conversation should continue
        :param temperature: The temperature parameter for controlling randomness (0.0-1.0)
        :param seed: Optional seed for deterministic generation
        :param extra_kwargs: Additional keyword arguments for API call
        :return: A tuple containing the response content and finish reason
        """
        retry_cnt = 0
        while retry_cnt < self.max_retry:
            try:                
                content = self._make_content(user_prompt, to_continue)
                
                # Add temperature and seed if provided
                if temperature is not None:
                    extra_kwargs['temperature'] = temperature
                if seed is not None:
                    extra_kwargs['seed'] = seed
                
                # Remove generation parameters that aren't supported in async API
                clean_kwargs = extra_kwargs.copy()
                for param in ['top_p', 'top_k', 'max_output_tokens']:
                    if param in clean_kwargs:
                        clean_kwargs.pop(param)
                
                response = await chat_completion_acreate(content=content, **clean_kwargs)
                full_content = response.text
                finish_reason = "stop"  # Gemini doesn't provide finish reason
                
                # Store conversation for context
                self.chat_log.append({"role": "user", "parts": [user_prompt]})                
                self.chat_log.append({"role": "model", "parts": [full_content]})
                
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
        temperature: float = 0.0,
        seed: int = None,
        **extra_kwargs
    ) -> Iterable[Tuple[str, str]]:
        """
        Get streaming response from the model synchronously.
        :param user_prompt: The user's input
        :param to_continue: Flag indicating if the conversation should continue
        :param temperature: The temperature parameter for controlling randomness (0.0-1.0)
        :param seed: Optional seed for deterministic generation
        :param extra_kwargs: Additional keyword arguments for API call
        :return Generator yields a tuple of content chunks and stop reason
        """
        try:
            content = self._make_content(user_prompt, to_continue)
            
            # Set stream=True
            extra_kwargs['stream'] = True
            
            # Add temperature and seed if provided
            if temperature is not None:
                extra_kwargs['temperature'] = temperature
            if seed is not None:
                extra_kwargs['seed'] = seed
            
            # Get model configuration if available
            if hasattr(conf, 'MODEL_CONFIG') and self.model_name in conf.MODEL_CONFIG:
                extra_kwargs.update(conf.MODEL_CONFIG[self.model_name])
            
            # Create a new model instance for this streaming session
            response = chat_completion_create(content=content, **extra_kwargs)
            
            full_content = ""
            # Gemini handles streaming differently from OpenAI
            for chunk in response:
                content_chunk = chunk.text or ""
                full_content += content_chunk
                yield content_chunk, None  # Gemini doesn't provide finish reason per chunk
            
            # After all chunks, store the full conversation
            self.chat_log.append({"role": "user", "parts": [user_prompt]})
            self.chat_log.append({"role": "model", "parts": [full_content]})
            
        except Exception as e:
            print(f"Error in streaming response: {e}")
            yield (f"Error: {str(e)}", "error")    
    async def get_stream_aresponse(
        self,
        user_prompt: str,
        to_continue: bool = False,
        temperature: float = 0.0,
        seed: int = None,
        **extra_kwargs
    ) -> AsyncIterable[Tuple[str, str]]:
        """
        Get streaming response from the model asynchronously.
        :param user_prompt: The user's input
        :param to_continue: Flag indicating if the conversation should continue
        :param temperature: The temperature parameter for controlling randomness (0.0-1.0)
        :param seed: Optional seed for deterministic generation
        :param extra_kwargs: Additional keyword arguments for API call
        :return AsyncGenerator yields a tuple of content chunks and stop reason
        """
        retry_count = 0
        max_retry = 3  # Maximum retries for API issues
        
        while retry_count < max_retry:
            try:            
                # Prepare content
                content = self._make_content(user_prompt, to_continue)
                
                # Set stream=True
                extra_kwargs['stream'] = True
                
                # Add temperature and seed directly to the API call
                if temperature is not None:
                    extra_kwargs['temperature'] = temperature
                if seed is not None:
                    extra_kwargs['seed'] = seed
                
                # Remove any generation config parameters that cause errors with generate_content_async
                for param in ['top_p', 'top_k', 'max_output_tokens']:
                    if param in extra_kwargs:
                        extra_kwargs.pop(param)
                
                # Get model configuration if available, but remove any parameters
                # that are incompatible with the async API
                if hasattr(conf, 'MODEL_CONFIG') and self.model_name in conf.MODEL_CONFIG:
                    # For async calls, we need to exclude all generation config parameters
                    # as they're not supported by generate_content_async
                    async_safe_kwargs = {}
                    for key, value in conf.MODEL_CONFIG[self.model_name].items():
                        # Only pass parameters that aren't generation config
                        if key not in ['temperature', 'top_p', 'top_k', 'max_output_tokens']:
                            async_safe_kwargs[key] = value
                            
                    extra_kwargs.update(async_safe_kwargs)
                
                # Use existing event loop for API calls
                response = await chat_completion_acreate(content=content, **extra_kwargs)
                
                full_content = ""
                # Process streaming response
                async for chunk in response:
                    content_chunk = chunk.text or ""
                    full_content += content_chunk
                    yield content_chunk, None  # Gemini doesn't provide finish reason per chunk
                
                # After all chunks, store the full conversation
                self.chat_log.append({"role": "user", "parts": [user_prompt]})
                self.chat_log.append({"role": "model", "parts": [full_content]})
                
                # If we get here, streaming completed successfully
                break
                
            except Exception as e:
                retry_count += 1
                print(f"Error in streaming response: {e} | Retry: {retry_count}/{max_retry}")
                
                if retry_count >= max_retry:
                    print("Maximum retries reached")
                    yield (f"Error: {str(e)}", "error")
                    break
                
                # Add a small delay before retrying
                await asyncio.sleep(1)

async def translate_text_entry(
        text: str, 
        source_lang: str, 
        target_lang: str, 
        mapping_table: dict, 
        software_type: str, 
        image_path: Optional[str] = None,
        model_name: str = None,
        is_batch: bool = False,
        preserve_newlines: bool = True,
        temperature: float = 0.0,
        seed: int = None
    ) -> str:
    """
    Translate a single text entry or a batch of text entries using the Gemini translation model.
    
    :param text: Text to translate or JSON string for batch translation
    :param source_lang: Source language
    :param target_lang: Target language
    :param mapping_table: Dictionary with specific name translations
    :param software_type: Type of software being translated
    :param image_path: Optional path to images for translation enhancement
    :param model_name: Optional model name override
    :param is_batch: Whether the input is a batch of text entries in JSON format
    :param preserve_newlines: Whether to explicitly preserve newlines in the translation
    :param temperature: The temperature parameter for controlling randomness (0.0-1.0)
    :param seed: Optional seed for deterministic generation
    :return: Translated text or JSON string for batch translation
    """
    if not text or str(text).strip() == '':
        return ''
    
    # Get the model name from config if not specified
    if not model_name:
        model_name = conf.GEMINI_VISION_MODEL
    
    # Initialize the chat with appropriate system prompt
    from prompts.translate_prompts import translate_sys_prompt
    chat = GeminiAPIChat(
        model_name=model_name,
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
    try:
        # Create appropriate prompt based on whether it's batch or single
        if is_batch:
            # Batch translation prompt with emphasis on preserving newlines
            prompt = f"""Translate the following text from {source_lang} to {target_lang}.
"""
            if preserve_newlines:
                prompt += """IMPORTANT: You MUST preserve all line breaks (\\n), bullet points, and formatting exactly as they appear in the original text.
"""
            prompt += f"""The input is a JSON object where each key points to a text that needs translation.
Output the translation as a JSON object with the same keys.
"""
            if preserve_newlines:
                prompt += """Each newline character must be preserved in exactly the same position in the translated text.

"""
            prompt += text  # Add the JSON text
            
        else:
            # Single text translation prompt
            prompt = f"Please translate the following text from {source_lang} to {target_lang}:"
            if preserve_newlines:
                prompt += "\nIMPORTANT: You MUST preserve all line breaks (\\n) exactly as they appear in the original text."
            prompt += f"\n\n{text}"
        
        # Add specific names guidance if available
        if relevant_specific_names:
            prompt += "\n\nPlease use the following specific translations for terms:\n"
            for source_term, target_term in relevant_specific_names.items():
                prompt += f"- '{source_term}' → '{target_term}'\n"
                
        # Get streaming response with temperature and seed
        async for chunk, stop_reason in chat.get_stream_aresponse(prompt, temperature=temperature, seed=seed):
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
    except Exception as e:
        print(f"Error translating text: {e}")
        return f"ERROR: {str(e)[:100]}"
    finally:
        # Always clean up resources
        try:
            await chat.close()  # Use the new explicit close method
        except Exception as close_err:
            print(f"Error closing chat: {close_err}")
        
    return response
