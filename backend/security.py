"""
Enhanced Cybersecurity Module for Law Firm Management System
Implements comprehensive security measures with simple installation
"""

import os
import re
import time
import hashlib
import secrets
import logging
import ipaddress
from typing import Dict, List, Optional, Set, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
import jwt
from passlib.context import CryptContext
import asyncio
from dataclasses import dataclass
import json

# Configure logging for security events
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Create file handler for security logs
security_handler = logging.FileHandler('/var/log/security_events.log')
security_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - SECURITY - %(levelname)s - %(message)s')
security_handler.setFormatter(formatter)
security_logger.addHandler(security_handler)

@dataclass
class SecurityEvent:
    event_type: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict
    severity: str = "INFO"  # INFO, WARNING, CRITICAL

class SecurityConfig:
    """Centralized security configuration"""
    
    # Rate Limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_DURATION = 900  # 15 minutes
    MAX_REQUESTS_PER_MINUTE = 100
    MAX_REQUESTS_PER_HOUR = 1000
    
    # Password Policy
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    PASSWORD_HISTORY_COUNT = 5
    PASSWORD_EXPIRY_DAYS = 90
    
    # Session Security
    SESSION_TIMEOUT_MINUTES = 30
    MAX_CONCURRENT_SESSIONS = 3
    REQUIRE_2FA_FOR_ADMIN = True
    
    # IP Security
    ENABLE_GEO_BLOCKING = False
    BLOCKED_COUNTRIES = ['CN', 'RU', 'KP']  # Example blocked countries
    WHITELIST_IPS = ['127.0.0.1', '::1']  # Always allowed IPs
    
    # File Security
    ALLOWED_FILE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.jpg', '.png', '.txt']
    MAX_FILE_SIZE_MB = 10
    SCAN_UPLOADED_FILES = True
    
    # SQL Injection Protection
    ENABLE_SQL_INJECTION_DETECTION = True
    
    # XSS Protection
    ENABLE_XSS_DETECTION = True

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)
    
    def is_rate_limited(self, ip: str, endpoint: str = "general") -> bool:
        """Check if IP is rate limited"""
        current_time = datetime.now()
        
        # Check if IP is temporarily blocked
        if ip in self.blocked_ips:
            if current_time < self.blocked_ips[ip]:
                return True
            else:
                del self.blocked_ips[ip]
        
        # Clean old requests (older than 1 hour)
        self.requests[ip] = deque([
            req_time for req_time in self.requests[ip] 
            if current_time - req_time < timedelta(hours=1)
        ])
        
        # Check hourly limit
        if len(self.requests[ip]) >= SecurityConfig.MAX_REQUESTS_PER_HOUR:
            self._block_ip(ip, minutes=60)
            return True
        
        # Check minute limit
        recent_requests = [
            req_time for req_time in self.requests[ip]
            if current_time - req_time < timedelta(minutes=1)
        ]
        
        if len(recent_requests) >= SecurityConfig.MAX_REQUESTS_PER_MINUTE:
            self._block_ip(ip, minutes=5)
            return True
        
        # Add current request
        self.requests[ip].append(current_time)
        return False
    
    def _block_ip(self, ip: str, minutes: int):
        """Block IP for specified duration"""
        self.blocked_ips[ip] = datetime.now() + timedelta(minutes=minutes)
        security_logger.warning(f"IP {ip} blocked for {minutes} minutes due to rate limiting")

class LoginAttemptTracker:
    """Track and prevent brute force attacks"""
    
    def __init__(self):
        self.failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self.locked_accounts: Dict[str, datetime] = {}
    
    def record_failed_attempt(self, identifier: str, ip: str) -> bool:
        """Record failed login attempt and return if account should be locked"""
        current_time = datetime.now()
        
        # Clean old attempts (older than 1 hour)
        self.failed_attempts[identifier] = [
            attempt_time for attempt_time in self.failed_attempts[identifier]
            if current_time - attempt_time < timedelta(hours=1)
        ]
        
        self.failed_attempts[identifier].append(current_time)
        
        # Check if account should be locked
        if len(self.failed_attempts[identifier]) >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            self._lock_account(identifier)
            security_logger.warning(
                f"Account {identifier} locked due to multiple failed login attempts from {ip}"
            )
            return True
        
        return False
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is locked"""
        if identifier in self.locked_accounts:
            if datetime.now() < self.locked_accounts[identifier]:
                return True
            else:
                del self.locked_accounts[identifier]
        return False
    
    def _lock_account(self, identifier: str):
        """Lock account for specified duration"""
        self.locked_accounts[identifier] = (
            datetime.now() + timedelta(seconds=SecurityConfig.LOGIN_LOCKOUT_DURATION)
        )
    
    def record_successful_login(self, identifier: str):
        """Clear failed attempts on successful login"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]

class PasswordValidator:
    """Comprehensive password validation"""
    
    @staticmethod
    def validate_password(password: str, username: str = "") -> tuple[bool, List[str]]:
        """Validate password against security policy"""
        errors = []
        
        # Length check
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters long")
        
        # Character requirements
        if SecurityConfig.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if SecurityConfig.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if SecurityConfig.REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if SecurityConfig.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Common password patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin']:
            errors.append("Password is too common")
        
        # Username similarity
        if username and username.lower() in password.lower():
            errors.append("Password cannot contain username")
        
        # Dictionary words (basic check)
        common_words = ['password', 'admin', 'user', 'login', 'system']
        if any(word in password.lower() for word in common_words):
            errors.append("Password contains common dictionary words")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a cryptographically secure password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

class SQLInjectionDetector:
    """Detect potential SQL injection attempts"""
    
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
        r"(--|\#|\/\*|\*\/)",
        r"(\b(CHAR|ASCII|SUBSTRING|LENGTH|MID)\s*\()",
        r"(\'\s*(OR|AND)\s*\'\d+\'\s*=\s*\'\d+)",
        r"(\bEXEC\s*\(\s*CHAR\s*\()",
    ]
    
    @classmethod
    def detect_sql_injection(cls, input_string: str) -> bool:
        """Detect potential SQL injection in input"""
        if not SecurityConfig.ENABLE_SQL_INJECTION_DETECTION:
            return False
        
        input_upper = input_string.upper()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_upper, re.IGNORECASE):
                security_logger.critical(f"SQL Injection attempt detected: {input_string[:100]}")
                return True
        
        return False

class XSSDetector:
    """Detect potential XSS attempts"""
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    @classmethod
    def detect_xss(cls, input_string: str) -> bool:
        """Detect potential XSS in input"""
        if not SecurityConfig.ENABLE_XSS_DETECTION:
            return False
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                security_logger.critical(f"XSS attempt detected: {input_string[:100]}")
                return True
        
        return False

class SecurityHeaders:
    """Security headers for HTTP responses"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://apis.google.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.example.com"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "magnetometer=(), gyroscope=(), payment=()"
            )
        }

class FileValidator:
    """Validate uploaded files for security"""
    
    DANGEROUS_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', 
        '.jar', '.php', '.asp', '.aspx', '.jsp', '.py', '.pl', '.rb'
    ]
    
    @classmethod
    def validate_file(cls, filename: str, file_content: bytes) -> tuple[bool, List[str]]:
        """Validate uploaded file"""
        errors = []
        
        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext in cls.DANGEROUS_EXTENSIONS:
            errors.append(f"File type {file_ext} is not allowed")
        
        if file_ext not in SecurityConfig.ALLOWED_FILE_EXTENSIONS:
            errors.append(f"File type {file_ext} is not in allowed list")
        
        # Check file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > SecurityConfig.MAX_FILE_SIZE_MB:
            errors.append(f"File size ({file_size_mb:.1f}MB) exceeds limit ({SecurityConfig.MAX_FILE_SIZE_MB}MB)")
        
        # Basic malware detection (simple signature checking)
        if cls._contains_malware_signatures(file_content):
            errors.append("File contains suspicious content")
        
        return len(errors) == 0, errors
    
    @classmethod
    def _contains_malware_signatures(cls, content: bytes) -> bool:
        """Basic malware signature detection"""
        # Common malware signatures (simplified)
        suspicious_patterns = [
            b'MZ\x90\x00',  # PE executable header
            b'PK\x03\x04',  # ZIP file (could contain scripts)
        ]
        
        # Only check for PE executables in non-executable files
        if content.startswith(b'MZ'):
            return True
        
        return False

class SecurityManager:
    """Main security manager orchestrating all security components"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.login_tracker = LoginAttemptTracker()
        self.security_events: List[SecurityEvent] = []
        self._load_security_config()
    
    def _load_security_config(self):
        """Load security configuration from environment or file"""
        # Override config from environment variables
        SecurityConfig.MAX_LOGIN_ATTEMPTS = int(os.environ.get('SEC_MAX_LOGIN_ATTEMPTS', 5))
        SecurityConfig.SESSION_TIMEOUT_MINUTES = int(os.environ.get('SEC_SESSION_TIMEOUT', 30))
        
    def log_security_event(self, event: SecurityEvent):
        """Log security event"""
        self.security_events.append(event)
        security_logger.log(
            getattr(logging, event.severity),
            f"{event.event_type} from {event.ip_address}: {event.details}"
        )
    
    def validate_request(self, request: Request) -> bool:
        """Comprehensive request validation"""
        client_ip = self._get_client_ip(request)
        
        # Rate limiting check
        if self.rate_limiter.is_rate_limited(client_ip):
            self.log_security_event(SecurityEvent(
                event_type="RATE_LIMIT_EXCEEDED",
                ip_address=client_ip,
                user_agent=request.headers.get("User-Agent", "Unknown"),
                timestamp=datetime.now(),
                details={"endpoint": str(request.url.path)},
                severity="WARNING"
            ))
            return False
        
        return True
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def generate_security_report(self) -> Dict:
        """Generate security report"""
        current_time = datetime.now()
        last_24h = current_time - timedelta(hours=24)
        
        recent_events = [
            event for event in self.security_events
            if event.timestamp >= last_24h
        ]
        
        return {
            "report_generated": current_time.isoformat(),
            "total_events_24h": len(recent_events),
            "events_by_type": {
                event_type: len([e for e in recent_events if e.event_type == event_type])
                for event_type in set(e.event_type for e in recent_events)
            },
            "blocked_ips": len(self.rate_limiter.blocked_ips),
            "locked_accounts": len(self.login_tracker.locked_accounts),
            "security_config": {
                "max_login_attempts": SecurityConfig.MAX_LOGIN_ATTEMPTS,
                "session_timeout": SecurityConfig.SESSION_TIMEOUT_MINUTES,
                "rate_limit_per_minute": SecurityConfig.MAX_REQUESTS_PER_MINUTE,
            }
        }

# Global security manager instance
security_manager = SecurityManager()

# Security middleware functions
async def security_middleware(request: Request):
    """FastAPI middleware for security checks"""
    if not security_manager.validate_request(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

def validate_input_security(input_data: str) -> bool:
    """Validate input for security threats"""
    if SQLInjectionDetector.detect_sql_injection(input_data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input detected"
        )
    
    if XSSDetector.detect_xss(input_data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input detected"
        )
    
    return True

# Enhanced password hashing
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=1,
)

def hash_password(password: str) -> str:
    """Hash password with Argon2"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with constant-time comparison"""
    return pwd_context.verify(plain_password, hashed_password)