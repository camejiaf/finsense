"""
Security middleware and utilities for FinSense
Professional security headers and HTTPS enforcement
"""

from fastapi import Request, HTTPException
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog
from typing import Dict, Any

# Configure structured logging
logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with security context"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(
            "request_started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )

        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            client_ip=request.client.host if request.client else "unknown"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting with IP and user tracking"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old requests
        if client_ip in self.clients:
            self.clients[client_ip] = [
                req_time for req_time in self.clients[client_ip]
                if current_time - req_time < self.period
            ]
        else:
            self.clients[client_ip] = []

        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                requests=len(self.clients[client_ip]),
                limit=self.calls
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Too many requests from this IP.",
                headers={"Retry-After": str(self.period)}
            )

        # Add current request
        self.clients[client_ip].append(current_time)

        response = await call_next(request)
        return response


def validate_api_key(api_key: str) -> bool:
    """Validate API key format and structure"""
    if not api_key:
        return False

    # Basic validation - in production, check against database
    if len(api_key) < 32:
        return False

    return True


def sanitize_input(data: Any) -> Any:
    """Sanitize user input to prevent injection attacks"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'",
                           '&', ';', '(', ')', '|', '`', '$']
        for char in dangerous_chars:
            data = data.replace(char, '')
        return data.strip()

    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}

    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]

    return data


def check_suspicious_activity(request: Request) -> bool:
    """Check for suspicious request patterns"""
    # Check for common attack patterns
    suspicious_patterns = [
        '../', '..\\', 'script:', 'javascript:', 'data:',
        'union select', 'drop table', 'insert into',
        '<script', 'eval(', 'exec('
    ]

    # Check URL
    url_lower = str(request.url).lower()
    for pattern in suspicious_patterns:
        if pattern in url_lower:
            logger.warning(
                "suspicious_request_detected",
                pattern=pattern,
                url=str(request.url),
                client_ip=request.client.host if request.client else "unknown"
            )
            return True

    # Check headers
    user_agent = request.headers.get("user-agent", "").lower()
    if any(pattern in user_agent for pattern in ['bot', 'crawler', 'spider']):
        logger.info(
            "bot_request_detected",
            user_agent=user_agent,
            client_ip=request.client.host if request.client else "unknown"
        )

    return False

