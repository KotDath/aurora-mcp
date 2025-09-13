"""
Copyright 2025 Daniil Markevich (KotDath)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import asyncio
from enum import Enum
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class DevelopmentStatus(Enum):
    """Development status for functions and tools."""

    READY = "ready"
    NOT_READY = "not_ready"


def development_status(status: DevelopmentStatus) -> Callable[[F], F]:
    """Mark a function with its development status.

    Args:
        status: Development status (ready or not_ready)

    Returns:
        Decorated function that returns "this function is not ready yet"
        if status is NOT_READY, otherwise returns the original function result
    """

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                if status == DevelopmentStatus.NOT_READY:
                    return {
                        "status": "not_ready",
                        "message": "this function is not ready yet",
                    }
                return await func(*args, **kwargs)

            # Preserve function metadata
            async_wrapper.__name__ = func.__name__
            async_wrapper.__doc__ = func.__doc__
            async_wrapper.__development_status__ = status

            return async_wrapper  # type: ignore
        else:

            def sync_wrapper(*args, **kwargs):
                if status == DevelopmentStatus.NOT_READY:
                    return {
                        "status": "not_ready",
                        "message": "this function is not ready yet",
                    }
                return func(*args, **kwargs)

            # Preserve function metadata
            sync_wrapper.__name__ = func.__name__
            sync_wrapper.__doc__ = func.__doc__
            sync_wrapper.__development_status__ = status

            return sync_wrapper  # type: ignore

    return decorator
