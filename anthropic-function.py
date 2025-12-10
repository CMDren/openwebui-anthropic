"""
title: Anthropic Manifold Pipe
authors: justinh-rahb and christian-taillon and soeren weber
author_url: https://github.com/CMDren
funding_url: https://github.com/open-webui
version: 0.4.0
required_open_webui_version: 0.3.17
license: MIT
"""

import os
import requests
import json
import logging
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field
from open_webui.utils.misc import pop_system_message

# Configure logging
logger = logging.getLogger(__name__)


class Pipe:
    class Valves(BaseModel):
        ANTHROPIC_API_KEY: str = Field(
            default="",
            description="Anthropic API Key"
        )
        ANTHROPIC_API_VERSION: str = Field(
            default="2023-06-01",
            description="API version header"
        )
        MAX_TOKENS: int = Field(
            default=4096,
            description="Default max tokens"
        )
        TEMPERATURE: float = Field(
            default=1.0,
            description="Default temperature (0.0-1.0)"
        )
        REQUEST_TIMEOUT: int = Field(
            default=60,
            description="Request timeout in seconds"
        )
        CONNECTION_TIMEOUT: float = Field(
            default=3.05,
            description="Connection timeout in seconds"
        )

    def __init__(self):
        self.type = "manifold"
        self.id = "anthropic"
        self.name = "anthropic/"
        self.valves = self.Valves(
            **{"ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "")}
        )
        self.MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB per image
        self.MAX_TOTAL_IMAGE_SIZE = 100 * 1024 * 1024  # 100MB total

    def get_anthropic_models(self):
        return [
            {"id": "claude-sonnet-4-5-20250929", "name": "claude-sonnet-4.5"},
            {"id": "claude-haiku-4-5-20251001", "name": "claude-haiku-4.5"},
            {"id": "claude-opus-4-5-20251101", "name": "claude-opus-4.5"},
        ]

    def pipes(self) -> List[dict]:
        return self.get_anthropic_models()

    def _extract_model_id(self, model_string: str) -> str:
        """Extract model ID from model string, handling various formats."""
        if not model_string:
            raise ValueError("Model string is empty")
        
        # If contains ".", extract part after it (e.g., "anthropic.claude-opus-4-5")
        if "." in model_string:
            return model_string.split(".", 1)[1]
        
        # Otherwise use as-is
        return model_string

    def process_image(self, image_data: dict) -> dict:
        """Process image data with size validation."""
        try:
            url = image_data["image_url"]["url"]
            
            if url.startswith("data:image"):
                # Base64 encoded image
                mime_type, base64_data = url.split(",", 1)
                media_type = mime_type.split(":")[1].split(";")[0]

                # Check base64 image size
                image_size = len(base64_data) * 3 / 4
                if image_size > self.MAX_IMAGE_SIZE:
                    raise ValueError(
                        f"Image size exceeds 5MB limit: {image_size / (1024 * 1024):.2f}MB"
                    )

                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_data,
                    },
                }
            else:
                # URL image - check size
                try:
                    response = requests.head(url, allow_redirects=True, timeout=5)
                    content_length = int(response.headers.get("content-length", 0))

                    if content_length > self.MAX_IMAGE_SIZE:
                        raise ValueError(
                            f"Image at URL exceeds 5MB limit: {content_length / (1024 * 1024):.2f}MB"
                        )
                except requests.RequestException as e:
                    logger.warning(f"Could not verify image size at {url}: {e}")
                    # Continue anyway - Anthropic will validate

                return {
                    "type": "image",
                    "source": {"type": "url", "url": url},
                }
        except (KeyError, ValueError) as e:
            logger.error(f"Error processing image: {e}")
            raise

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        # Validate API key
        if not self.valves.ANTHROPIC_API_KEY:
            return "Error: ANTHROPIC_API_KEY not configured"

        system_message, messages = pop_system_message(body["messages"])

        processed_messages = []
        total_image_size = 0

        for message in messages:
            processed_content = []
            
            if isinstance(message.get("content"), list):
                for item in message["content"]:
                    if item["type"] == "text":
                        processed_content.append({"type": "text", "text": item["text"]})
                    elif item["type"] == "image_url":
                        try:
                            processed_image = self.process_image(item)
                            processed_content.append(processed_image)

                            # Track total size for base64 images
                            if processed_image["source"]["type"] == "base64":
                                image_size = len(processed_image["source"]["data"]) * 3 / 4
                                total_image_size += image_size
                                if total_image_size > self.MAX_TOTAL_IMAGE_SIZE:
                                    raise ValueError(
                                        f"Total image size exceeds 100MB limit: {total_image_size / (1024 * 1024):.2f}MB"
                                    )
                        except Exception as e:
                            logger.error(f"Failed to process image: {e}")
                            return f"Error: Failed to process image: {e}"
            else:
                processed_content = [
                    {"type": "text", "text": message.get("content", "")}
                ]

            processed_messages.append(
                {"role": message["role"], "content": processed_content}
            )

        # Build payload
        try:
            model_id = self._extract_model_id(body["model"])
        except Exception as e:
            return f"Error: Invalid model format: {e}"

        payload = {
            "model": model_id,
            "messages": processed_messages,
            "max_tokens": body.get("max_tokens", self.valves.MAX_TOKENS),
            "temperature": body.get("temperature", self.valves.TEMPERATURE),
            "stream": body.get("stream", False),
        }

        # Add optional parameters
        if body.get("stop"):
            payload["stop_sequences"] = body["stop"]
        
        if system_message:
            payload["system"] = str(system_message)

        headers = {
            "x-api-key": self.valves.ANTHROPIC_API_KEY,
            "anthropic-version": self.valves.ANTHROPIC_API_VERSION,
            "content-type": "application/json",
        }

        url = "https://api.anthropic.com/v1/messages"

        try:
            if body.get("stream", False):
                return self.stream_response(url, headers, payload)
            else:
                return self.non_stream_response(url, headers, payload)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return f"Error: Request failed: {e}"
        except Exception as e:
            logger.error(f"Error in pipe method: {e}")
            return f"Error: {e}"

    def stream_response(self, url: str, headers: dict, payload: dict) -> Generator:
        """Handle streaming response from Anthropic API."""
        try:
            timeout = (self.valves.CONNECTION_TIMEOUT, self.valves.REQUEST_TIMEOUT)
            
            with requests.post(
                url, headers=headers, json=payload, stream=True, timeout=timeout
            ) as response:
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"HTTP {response.status_code}: {error_text}")
                    yield f"Error: HTTP {response.status_code}: {error_text}"
                    return

                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                
                                # Handle different event types
                                if data["type"] == "content_block_delta":
                                    if "delta" in data and "text" in data["delta"]:
                                        yield data["delta"]["text"]
                                
                                elif data["type"] == "message_stop":
                                    break
                                
                                # Ignore content_block_start, message_start, etc.
                                
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON: {line[:100]}")
                            except KeyError as e:
                                logger.warning(f"Unexpected data structure: {e}")
                                
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            yield "Error: Request timeout"
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            yield f"Error: Request failed: {e}"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"Error: {e}"

    def non_stream_response(self, url: str, headers: dict, payload: dict) -> str:
        """Handle non-streaming response from Anthropic API."""
        try:
            timeout = (self.valves.CONNECTION_TIMEOUT, self.valves.REQUEST_TIMEOUT)
            
            response = requests.post(
                url, headers=headers, json=payload, timeout=timeout
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"HTTP {response.status_code}: {error_text}")
                return f"Error: HTTP {response.status_code}: {error_text}"

            res = response.json()
            
            # Extract text from response
            if "content" in res and res["content"]:
                for content in res["content"]:
                    if content.get("type") == "text":
                        return content.get("text", "")
            
            return ""
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return "Error: Request timeout"
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"Error: {e}"
