"""
Authentication Service
======================
Handles Angel One authentication and session management.

Features:
- OAuth/JWT login flow
- Token refresh
- Session validation
- Multi-client support
"""

from typing import Dict, Any, Optional

import pyotp
from SmartApi import SmartConnect

from ..utils.logging_utils import TradingLogger
from ..managers.session_manager import SessionManager, ClientSession

logger = TradingLogger("auth_service")


class AuthService:
    """
    Authentication service for Angel One API.
    
    Usage:
        auth = AuthService()
        result = auth.login(client_id, password, totp_secret, api_key)
        
        if result['status'] == 'success':
            session = auth.get_session(client_id)
    """
    
    def __init__(self):
        self._session_manager = SessionManager.get_instance()

    def resolve_login_credentials(
        self,
        *,
        client_id: Optional[str],
        password: Optional[str],
        totp_secret: Optional[str],
        api_key: Optional[str],
        broker_details=None,
    ) -> Dict[str, Optional[str]]:
        resolved_client_id = client_id.strip() if isinstance(client_id, str) and client_id.strip() else None
        resolved_password = password.strip() if isinstance(password, str) and password.strip() else None
        resolved_totp_secret = totp_secret.strip() if isinstance(totp_secret, str) and totp_secret.strip() else None
        resolved_api_key = api_key.strip() if isinstance(api_key, str) and api_key.strip() else None

        if broker_details:
            credentials = broker_details.get_angel_one_login_credentials()
            resolved_client_id = resolved_client_id or credentials.get("client_code")
            resolved_password = resolved_password or credentials.get("password")
            resolved_totp_secret = resolved_totp_secret or credentials.get("totp_secret")
            resolved_api_key = resolved_api_key or credentials.get("api_key")

        return {
            "client_id": resolved_client_id,
            "password": resolved_password,
            "totp_secret": resolved_totp_secret,
            "api_key": resolved_api_key,
        }
    
    def login(
        self,
        client_id: str,
        password: str,
        totp_secret: str,
        api_key: str,
        broker_details=None,
        force_new: bool = False,
        proxy_config: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Login to Angel One.
        
        Args:
            client_id: Angel One client ID
            password: Account password
            totp_secret: TOTP secret for 2FA
            api_key: API key
            broker_details: Optional Django model for token storage
            force_new: Force new login
            
        Returns:
            Dict with status and tokens
        """
        resolved = self.resolve_login_credentials(
            client_id=client_id,
            password=password,
            totp_secret=totp_secret,
            api_key=api_key,
            broker_details=broker_details,
        )

        # Validate inputs
        if not all([
            resolved["client_id"],
            resolved["password"],
            resolved["totp_secret"],
            resolved["api_key"],
        ]):
            return {
                "status": "error",
                "message": "Missing required credentials"
            }

        logger.info(
            "Login attempt",
            client_id=resolved["client_id"]
        )
        
        # Use session manager for login
        result = self._session_manager.login(
            client_id=resolved["client_id"],
            password=resolved["password"],
            totp_secret=resolved["totp_secret"],
            api_key=resolved["api_key"],
            force_new=force_new,
            proxy_config=proxy_config,
        )
        
        # Save to broker_details if provided
        if result.get("status") == "success" and broker_details:
            try:
                session = self._session_manager.get_session(resolved["client_id"], resolved["api_key"], proxy_config=proxy_config)
                if session:
                    broker_details.set_session_tokens(
                        access_token=session.access_token,
                        refresh_token=session.refresh_token,
                        feed_token=session.feed_token,
                        expiry=session.session_expiry,
                        mark_token_created=True,
                    )
                    broker_details.broker_last_logout_at = None
                    broker_details.clear_legacy_angel_sensitive_fields()
                    broker_details.save(update_fields=[
                        "encrypted_access_token",
                        "encrypted_refresh_token",
                        "encrypted_feed_token",
                        "access_token_expiry",
                        "isTokenExpired",
                        "tokenCreatedAt",
                        "broker_last_logout_at",
                        "access_token",
                        "refreshToken",
                        "feed_token",
                        "broker_pass",
                        "broker_Totp_Authcode",
                    ])
                
                logger.info(
                    "Broker details updated",
                    client_id=resolved["client_id"]
                )
            except Exception as e:
                logger.error(
                    "Failed to save broker details",
                    client_id=resolved["client_id"],
                    error=str(e)
                )
        
        return result
    
    def logout(
        self,
        client_id: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Logout client"""
        return self._session_manager.logout(client_id, api_key)

    def register_existing_tokens(
        self,
        client_id: str,
        api_key: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        feed_token: Optional[str] = None,
        broker_details=None,
        verify_remote: bool = True,
        proxy_config: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Register callback-provided tokens only after broker-side verification."""
        session = self._session_manager.create_session_from_tokens(
            client_id=client_id,
            api_key=api_key,
            access_token=access_token,
            refresh_token=refresh_token,
            feed_token=feed_token,
            session_expiry=getattr(broker_details, "access_token_expiry", None) if broker_details else None,
            remote_verified=False,
            persist=False,
            proxy_config=proxy_config,
        )
        if not session:
            return {"status": "error", "message": "Access token is required"}

        if verify_remote:
            self._session_manager.create_session_from_tokens(
                client_id=client_id,
                api_key=api_key,
                access_token=access_token,
                refresh_token=refresh_token,
                feed_token=feed_token,
                session_expiry=getattr(broker_details, "access_token_expiry", None) if broker_details else None,
                remote_verified=False,
                persist=True,
                proxy_config=proxy_config,
            )
            validation = self._session_manager.validate_session(
                client_id=client_id,
                api_key=api_key,
                broker_details=broker_details,
                verify_remote=True,
                proxy_config=proxy_config,
            )
            if validation.get("status") != "success":
                self._session_manager.invalidate_local_session(client_id=client_id, api_key=api_key, proxy_config=proxy_config)
                return validation
            session = validation.get("session")
        else:
            self._session_manager.create_session_from_tokens(
                client_id=client_id,
                api_key=api_key,
                access_token=access_token,
                refresh_token=refresh_token,
                feed_token=feed_token,
                session_expiry=getattr(broker_details, "access_token_expiry", None) if broker_details else None,
                remote_verified=False,
                persist=True,
                proxy_config=proxy_config,
            )

        if broker_details:
            broker_details.set_session_tokens(
                access_token=session.access_token,
                refresh_token=session.refresh_token,
                feed_token=session.feed_token,
                expiry=session.session_expiry,
                mark_token_created=True,
            )
            broker_details.broker_last_logout_at = None
            broker_details.clear_legacy_angel_sensitive_fields()
            broker_details.save(update_fields=[
                "encrypted_access_token",
                "encrypted_refresh_token",
                "encrypted_feed_token",
                "access_token_expiry",
                "isTokenExpired",
                "tokenCreatedAt",
                "broker_last_logout_at",
                "access_token",
                "refreshToken",
                "feed_token",
                "broker_pass",
                "broker_Totp_Authcode",
            ])

        return {
            "status": "success",
            "message": "Tokens registered",
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "session": session.to_dict(),
        }
    
    def refresh_session(
        self,
        client_id: str,
        api_key: Optional[str] = None,
        proxy_config: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Refresh session tokens"""
        return self._session_manager.refresh_session(client_id, api_key, proxy_config=proxy_config)
    
    def get_session(
        self,
        client_id: str,
        api_key: Optional[str] = None,
        proxy_config: Optional[Dict[str, str]] = None,
    ) -> Optional[ClientSession]:
        """Get client session"""
        return self._session_manager.get_session(client_id, api_key, proxy_config=proxy_config)
    
    def get_smart_connect(
        self,
        client_id: str,
        api_key: Optional[str] = None,
        proxy_config: Optional[Dict[str, str]] = None,
    ) -> Optional[SmartConnect]:
        """Get SmartConnect instance"""
        return self._session_manager.get_smart_connect(client_id, api_key, proxy_config=proxy_config)
    
    def is_session_valid(
        self,
        client_id: str,
        api_key: Optional[str] = None
    ) -> bool:
        """Check if session is valid"""
        session = self.get_session(client_id, api_key)
        return session is not None and session.is_valid()

    def ensure_valid_session(
        self,
        client_id: str,
        api_key: str,
        broker_details=None,
        verify_remote: bool = True,
        proxy_config: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Ensure a usable session exists by validating, refreshing, or rebuilding it."""
        result = self._session_manager.validate_session(
            client_id=client_id,
            api_key=api_key,
            broker_details=broker_details,
            verify_remote=verify_remote,
            proxy_config=proxy_config,
        )
        if result.get("status") == "success" and broker_details:
            session = result.get("session")
            if session:
                try:
                    broker_details.set_session_tokens(
                        access_token=session.access_token,
                        refresh_token=session.refresh_token,
                        feed_token=session.feed_token,
                        expiry=session.session_expiry,
                        mark_token_created=True,
                    )
                    broker_details.broker_last_logout_at = None
                    broker_details.clear_legacy_angel_sensitive_fields()
                    broker_details.save(update_fields=[
                        "encrypted_access_token",
                        "encrypted_refresh_token",
                        "encrypted_feed_token",
                        "access_token_expiry",
                        "isTokenExpired",
                        "tokenCreatedAt",
                        "broker_last_logout_at",
                        "access_token",
                        "refreshToken",
                        "feed_token",
                        "broker_pass",
                        "broker_Totp_Authcode",
                    ])
                except Exception as e:
                    logger.error("Failed to persist ensured session", client_id=client_id, error=str(e))
        return result
    
    def validate_credentials(
        self,
        client_id: str,
        password: str,
        totp_secret: str,
        api_key: str,
        proxy_config: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Validate credentials without creating session.
        
        Returns:
            Dict with validation result
        """
        try:
            # Generate TOTP
            totp = pyotp.TOTP(totp_secret).now()
            
            # Try to create session
            obj = SmartConnect(api_key=api_key, proxies=proxy_config)
            data = obj.generateSession(client_id, password, totp)
            
            if data.get("status"):
                # Logout immediately
                try:
                    obj.terminateSession(client_id)
                except:
                    pass
                
                return {
                    "status": "success",
                    "message": "Credentials are valid"
                }
            else:
                return {
                    "status": "error",
                    "message": data.get("message", "Invalid credentials")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_profile(
        self,
        client_id: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user profile"""
        session = self.get_session(client_id, api_key)
        smart_connect = session.smart_connect if session else None
        
        if not smart_connect or not session or not session.refresh_token:
            return {
                "status": "error",
                "message": "No valid session"
            }
        
        try:
            data = smart_connect.getProfile(session.refresh_token)
            
            if data.get("status"):
                return {
                    "status": "success",
                    "data": data.get("data", {})
                }
            else:
                return {
                    "status": "error",
                    "message": data.get("message", "Failed to get profile")
                }
                
        except Exception as e:
            logger.error(
                "Get profile failed",
                client_id=client_id,
                error=str(e)
            )
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_margin(
        self,
        client_id: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get margin/RMS limits"""
        smart_connect = self.get_smart_connect(client_id, api_key)
        
        if not smart_connect:
            return {
                "status": "error",
                "message": "No valid session"
            }
        
        try:
            data = smart_connect.rmsLimit()
            
            if data.get("status"):
                return {
                    "status": "success",
                    "data": data.get("data", {})
                }
            else:
                return {
                    "status": "error",
                    "message": data.get("message", "Failed to get margin")
                }
                
        except Exception as e:
            logger.error(
                "Get margin failed",
                client_id=client_id,
                error=str(e)
            )
            return {
                "status": "error",
                "message": str(e)
            }
