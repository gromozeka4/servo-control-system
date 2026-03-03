#!/usr/bin/env python3
"""
Network Utilities Module
Handles domain name resolution, IP address management, and network configuration.
"""

import socket
import time
import logging
from typing import Optional, Dict, List
from urllib.parse import urlparse
import threading
import cachetools


class NetworkManager:
    """
    Manages network configuration, domain resolution, and URL generation.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize network manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Network configuration
        self.local_network = config.get('local_network', {})
        self.domain_config = config.get('domain_config', {})
        
        # Resolved addresses cache
        self.address_cache = cachetools.TTLCache(
            maxsize=100,
            ttl=self.domain_config.get('cache_duration', 30) * 60
        )
        
        # Current resolved address
        self.current_address = None
        self.current_address_type = None  # 'ip' or 'domain'
        
        # Initialize network configuration
        self._initialize_network()
    
    def _initialize_network(self):
        """Initialize network configuration and resolve initial address."""
        try:
            # Try to get domain name first
            domain_name = self.local_network.get('pi_domain_name')
            if domain_name and domain_name != "YOUR_PI_IP_HERE":
                self.logger.info(f"Using domain name: {domain_name}")
                resolved_ip = self.resolve_domain(domain_name)
                if resolved_ip:
                    self.current_address = domain_name
                    self.current_address_type = 'domain'
                    self.logger.info(f"Domain {domain_name} resolved to {resolved_ip}")
                    return
            
            # Fallback to IP address
            ip_address = self.local_network.get('pi_ip_address')
            if ip_address and ip_address != "YOUR_PI_IP_HERE":
                self.current_address = ip_address
                self.current_address_type = 'ip'
                self.logger.info(f"Using IP address: {ip_address}")
                return
            
            # No valid configuration found
            self.logger.warning("No valid network configuration found")
            self.current_address = None
            self.current_address_type = None
            
        except Exception as e:
            self.logger.error(f"Failed to initialize network: {e}")
            self.current_address = None
            self.current_address_type = None
    
    def resolve_domain(self, domain_name: str) -> Optional[str]:
        """
        Resolve domain name to IP address.
        
        Args:
            domain_name: Domain name to resolve
            
        Returns:
            str: Resolved IP address or None if failed
        """
        try:
            # Check cache first
            if domain_name in self.address_cache:
                cached_ip = self.address_cache[domain_name]
                self.logger.debug(f"Using cached IP for {domain_name}: {cached_ip}")
                return cached_ip
            
            # Configure DNS servers if specified
            dns_servers = self.domain_config.get('dns_servers')
            if dns_servers:
                # Note: This is a simplified approach. For production use,
                # you might want to use a more robust DNS library
                self.logger.info(f"Using custom DNS servers: {dns_servers}")
            
            # Resolve domain
            timeout = self.domain_config.get('domain_timeout', 5)
            socket.setdefaulttimeout(timeout)
            
            resolved_ip = socket.gethostbyname(domain_name)
            
            # Cache the result
            self.address_cache[domain_name] = resolved_ip
            
            self.logger.info(f"Resolved {domain_name} to {resolved_ip}")
            return resolved_ip
            
        except socket.gaierror as e:
            self.logger.error(f"Failed to resolve domain {domain_name}: {e}")
            return None
        except socket.timeout:
            self.logger.error(f"Domain resolution timeout for {domain_name}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error resolving {domain_name}: {e}")
            return None
    
    def get_current_address(self) -> Optional[str]:
        """
        Get the current network address (domain or IP).
        
        Returns:
            str: Current address or None if not configured
        """
        return self.current_address
    
    def get_resolved_ip(self) -> Optional[str]:
        """
        Get the resolved IP address for the current network address.
        
        Returns:
            str: Resolved IP address or None if not available
        """
        if not self.current_address:
            return None
        
        if self.current_address_type == 'ip':
            return self.current_address
        elif self.current_address_type == 'domain':
            return self.resolve_domain(self.current_address)
        
        return None
    
    def get_api_base_url(self) -> str:
        """
        Get the base URL for API calls.
        
        Returns:
            str: Base URL for API
        """
        if not self.current_address:
            return "http://localhost:5000"
        
        return f"http://{self.current_address}:5000"
    
    def get_web_url(self) -> str:
        """
        Get the URL for the web interface.
        
        Returns:
            str: Web interface URL
        """
        if not self.current_address:
            return "http://localhost:8080"
        
        return f"http://{self.current_address}:8080"
    
    def refresh_address(self) -> bool:
        """
        Refresh the current network address (re-resolve domain if needed).
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.current_address_type == 'domain':
                resolved_ip = self.resolve_domain(self.current_address)
                if resolved_ip:
                    self.logger.info(f"Refreshed domain {self.current_address} -> {resolved_ip}")
                    return True
                else:
                    self.logger.warning(f"Failed to refresh domain {self.current_address}")
                    return False
            else:
                # IP address doesn't need refreshing
                return True
        except Exception as e:
            self.logger.error(f"Error refreshing address: {e}")
            return False
    
    def test_connectivity(self) -> Dict[str, bool]:
        """
        Test connectivity to the current address.
        
        Returns:
            Dict: Connectivity test results
        """
        results = {
            'api_server': False,
            'web_interface': False,
            'ping': False
        }
        
        if not self.current_address:
            return results
        
        try:
            # Test ping (basic connectivity)
            resolved_ip = self.get_resolved_ip()
            if resolved_ip:
                try:
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((resolved_ip, 22))
                    results['ping'] = True
                except:
                    results['ping'] = False
            
            # Test API server
            try:
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((resolved_ip or self.current_address, 5000))
                results['api_server'] = True
            except:
                results['api_server'] = False
            
            # Test web interface
            try:
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((resolved_ip or self.current_address, 8080))
                results['web_interface'] = True
            except:
                results['web_interface'] = False
                
        except Exception as e:
            self.logger.error(f"Error testing connectivity: {e}")
        
        return results
    
    def get_network_info(self) -> Dict:
        """
        Get comprehensive network information.
        
        Returns:
            Dict: Network information
        """
        resolved_ip = self.get_resolved_ip()
        connectivity = self.test_connectivity()
        
        return {
            'current_address': self.current_address,
            'address_type': self.current_address_type,
            'resolved_ip': resolved_ip,
            'api_url': self.get_api_base_url(),
            'web_url': self.get_web_url(),
            'connectivity': connectivity,
            'dns_servers': self.domain_config.get('dns_servers'),
            'cache_size': len(self.address_cache),
            'auto_resolve': self.domain_config.get('auto_resolve_domain', True)
        }


def resolve_domain_simple(domain_name: str, timeout: int = 5) -> Optional[str]:
    """
    Simple domain resolution function.
    
    Args:
        domain_name: Domain name to resolve
        timeout: Timeout in seconds
        
    Returns:
        str: Resolved IP address or None if failed
    """
    try:
        socket.setdefaulttimeout(timeout)
        return socket.gethostbyname(domain_name)
    except Exception:
        return None


def is_valid_ip(ip_address: str) -> bool:
    """
    Check if a string is a valid IP address.
    
    Args:
        ip_address: IP address string to validate
        
    Returns:
        bool: True if valid IP, False otherwise
    """
    try:
        socket.inet_aton(ip_address)
        return True
    except socket.error:
        return False


def is_valid_domain(domain_name: str) -> bool:
    """
    Check if a string is a valid domain name.
    
    Args:
        domain_name: Domain name string to validate
        
    Returns:
        bool: True if valid domain, False otherwise
    """
    # Simple domain validation
    if not domain_name or len(domain_name) > 253:
        return False
    
    # Check for valid characters
    valid_chars = set('abcdefghijklmnopqrstuvwxyz0123456789.-')
    return all(c.lower() in valid_chars for c in domain_name)
