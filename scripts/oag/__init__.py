"""
Okta Access Gateway API Management Module

This module provides Python clients and utilities for managing
Okta Access Gateway via its REST API.

Requires OAG version 2025.10.0 or later.
"""

from .oag_client import OAGClient
from .oag_applications import OAGApplicationManager

__all__ = ['OAGClient', 'OAGApplicationManager']
__version__ = '1.0.0'
