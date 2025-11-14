"""
Error Handler Module

Provides graceful error handling and recovery mechanisms.
"""

from typing import Optional, Dict, Any, Callable
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorHandler:
    """Handles errors gracefully with recovery and reporting"""
    
    @staticmethod
    def handle_file_not_found(file_path: str) -> Dict[str, Any]:
        """
        Handle file not found errors
        
        Args:
            file_path: Path that wasn't found
            
        Returns:
            Error info dict
        """
        import logging
        from datetime import datetime
        
        error_info = {
            'type': 'FILE_NOT_FOUND',
            'severity': ErrorSeverity.MEDIUM.value,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'message': f"File not found: {file_path}",
            'suggestions': [
                "Check if the file path is correct",
                "Verify file permissions",
                "Ensure the file hasn't been moved or deleted"
            ]
        }
        
        # Log the error
        logging.error(f"File not found: {file_path}")
        
        return error_info
    
    @staticmethod
    def handle_parse_error(file_path: str, error: Exception) -> Dict[str, Any]:
        """
        Handle file parsing errors
        
        Args:
            file_path: File that failed to parse
            error: Exception that occurred
            
        Returns:
            Error info dict
        """
        import logging
        from datetime import datetime
        
        error_info = {
            'type': 'PARSE_ERROR',
            'severity': ErrorSeverity.HIGH.value,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'message': f"Failed to parse {file_path}: {str(error)}",
            'exception_type': type(error).__name__,
            'exception_details': str(error),
            'suggestions': [
                "Check file syntax and formatting",
                "Validate YAML/JSON structure",
                "Ensure proper encoding (UTF-8)",
                "Look for special characters or formatting issues"
            ]
        }
        
        # Log the error
        logging.error(f"Parse error in {file_path}: {error}")
        
        return error_info
    
    @staticmethod
    def handle_validation_error(field: str, reason: str) -> Dict[str, Any]:
        """
        Handle validation errors
        
        Args:
            field: Field that failed validation
            reason: Reason for failure
            
        Returns:
            Error info dict
        """
        import logging
        from datetime import datetime
        
        error_info = {
            'type': 'VALIDATION_ERROR',
            'severity': ErrorSeverity.MEDIUM.value,
            'field': field,
            'timestamp': datetime.now().isoformat(),
            'message': f"Validation failed for '{field}': {reason}",
            'reason': reason,
            'suggestions': [
                f"Check the value for '{field}'",
                "Verify field format and constraints",
                "Consult documentation for valid values",
                "Use default values if available"
            ]
        }
        
        # Log the error
        logging.warning(f"Validation error for '{field}': {reason}")
        
        return error_info
    
    @staticmethod
    def handle_network_error(url: str, error: Exception) -> Dict[str, Any]:
        """
        Handle network/API errors
        
        Args:
            url: URL that failed
            error: Exception that occurred
            
        Returns:
            Error info dict
        """
        import logging
        from datetime import datetime
        
        error_info = {
            'type': 'NETWORK_ERROR',
            'severity': ErrorSeverity.HIGH.value,
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'message': f"Network request failed for {url}: {str(error)}",
            'exception_type': type(error).__name__,
            'exception_details': str(error),
            'suggestions': [
                "Check internet connection",
                "Verify URL is correct and accessible",
                "Check if service is temporarily down",
                "Verify API keys and authentication",
                "Try again after a short delay"
            ]
        }
        
        # Log the error
        logging.error(f"Network error for {url}: {error}")
        
        return error_info
    
    @staticmethod
    def with_retry(func: Callable, max_attempts: int = 3, backoff_seconds: int = 2) -> Any:
        """
        Retry a function with exponential backoff
        
        Args:
            func: Function to retry
            max_attempts: Maximum retry attempts
            backoff_seconds: Base backoff time
            
        Returns:
            Function result
        """
        import time
        import logging
        
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return func()
            except Exception as e:
                last_exception = e
                
                if attempt == max_attempts - 1:
                    # Final attempt failed
                    logging.error(f"Function failed after {max_attempts} attempts: {e}")
                    break
                
                # Calculate backoff time (exponential)
                sleep_time = backoff_seconds * (2 ** attempt)
                logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
        
        # All attempts failed, raise the last exception
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"Function failed after {max_attempts} attempts")
    
    @staticmethod
    def create_error_report(errors: list, output_path: str) -> None:
        """
        Create comprehensive error report
        
        Args:
            errors: List of error dicts
            output_path: Where to write report
        """
        import json
        from datetime import datetime
        from pathlib import Path
        
        try:
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Create comprehensive report
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_errors': len(errors),
                'error_summary': {},
                'errors': errors
            }
            
            # Generate error summary by type and severity
            for error in errors:
                error_type = error.get('type', 'UNKNOWN')
                severity = error.get('severity', 'unknown')
                
                if error_type not in report['error_summary']:
                    report['error_summary'][error_type] = {
                        'total': 0,
                        'by_severity': {}
                    }
                
                report['error_summary'][error_type]['total'] += 1
                
                if severity not in report['error_summary'][error_type]['by_severity']:
                    report['error_summary'][error_type]['by_severity'][severity] = 0
                report['error_summary'][error_type]['by_severity'][severity] += 1
            
            # Write report to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, separators=(',', ': '))
            
            print(f"Error report generated: {output_path}")
            
        except Exception as e:
            print(f"Failed to create error report: {e}")
