"""
Async Utilities Package

This package provides async/await compatibility helpers for different
Python and Discord library versions.
"""

import asyncio
import functools
import inspect
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TypeVar, Coroutine

# Define BackgroundTask class to avoid circular imports
class BackgroundTask:
    """A class to manage background tasks that run asynchronously"""
    
    def __init__(self, coro, name=None, loop=None):
        """Initialize a background task
        
        Args:
            coro: Coroutine to run
            name: Name of the task (default: None)
            loop: Event loop to use (default: None)
        """
        self.coro = coro
        self.name = name or "BackgroundTask"
        self.loop = loop or asyncio.get_event_loop()
        self.task = None
        self._running = False
        self._cancelled = False
        
    async def start(self):
        """Start the background task"""
        if self._running:
            return
            
        self._running = True
        self._cancelled = False
        self.task = asyncio.create_task(self._run())
        return self.task
        
    async def _run(self):
        """Run the task and handle errors"""
        try:
            await self.coro
        except asyncio.CancelledError:
            self._cancelled = True
        except Exception as e:
            logger.error(f"Error in background task {self.name}: {e}")
        finally:
            self._running = False
            
    def cancel(self):
        """Cancel the background task"""
        if not self._running or not self.task:
            return
            
        self.task.cancel()
        self._cancelled = True
        self._running = False
        
    @property
    def running(self):
        """Check if the task is running"""
        return self._running
        
    @property
    def cancelled(self):
        """Check if the task was cancelled"""
        return self._cancelled

# Setup logging
logger = logging.getLogger(__name__)

# Import async helpers from utils.async_helpers
from utils.async_helpers import (
    is_coroutine_function,
    ensure_async,
    ensure_sync,
    safe_gather,
    safe_wait,
    AsyncCache,
    cached_async
)

# Import type safety functions
from utils.type_safety import (
    safe_cast,
    safe_str,
    safe_int,
    safe_float,
    safe_bool,
    safe_list,
    safe_dict,
    safe_function_call,
    validate_type,
    validate_func_args
)

# Define retryable decorator here to avoid circular imports
def retryable(max_retries: int = 3, delay: float = 2.0, backoff: float = 1.5, 
              exceptions: Any = Exception):
    """Decorator for retrying failed async functions

    Args:
        max_retries: Maximum number of retries (default: 3)
        delay: Initial delay between retries in seconds (default: 2.0)
        backoff: Backoff multiplier (default: 1.5)
        exceptions: Exception type(s) to retry on (default: Exception)

    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay

            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Support for multiple exception types or single exception
                    should_retry = False

                    # Check if we should retry this exception
                    if isinstance(exceptions, (list, tuple)):
                        # Multiple exception types
                        for exc_type in exceptions:
                            if isinstance(e, exc_type):
                                should_retry = True
                                break
                    else:
                        # Single exception type
                        should_retry = isinstance(e, exceptions)

                    if not should_retry:
                        raise
                    retries += 1
                    if retries > max_retries:
                        # Max retries exceeded, re-raise exception
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                        raise

                    # Add jitter to delay (±20%)
                    jitter = random.uniform(0.8, 1.2)
                    wait_time = current_delay * jitter

                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} in {wait_time:.2f}s: {e}"
                    )

                    # Wait before retrying
                    await asyncio.sleep(wait_time)

                    # Increase delay for next retry
                    current_delay *= backoff

        return wrapper
    return decorator

# Additional async utilities can be imported from other files as needed
# But avoid circular imports by defining core functions inline

__all__ = [
    # Async helpers
    'is_coroutine_function',
    'ensure_async',
    'ensure_sync',
    'safe_gather',
    'safe_wait',
    'AsyncCache',
    'cached_async',
    
    # Retry and rate limiting
    'retryable',
    
    # Background tasks
    'BackgroundTask',
    
    # Type safety
    'safe_cast',
    'safe_str',
    'safe_int',
    'safe_float',
    'safe_bool',
    'safe_list',
    'safe_dict',
    'safe_function_call',
    'validate_type',
    'validate_func_args'
]