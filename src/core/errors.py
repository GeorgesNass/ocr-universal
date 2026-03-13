'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Dev"
__desc__ = "Centralized custom exceptions and structured helpers for the OCR Universal pipeline."
'''

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from src.utils.logging_utils import get_logger

## ============================================================
## LOGGER
## ============================================================
logger = get_logger("errors")

## ============================================================
## ERROR CODES
## ============================================================
ERROR_CODE_CONFIGURATION = "configuration_error"
ERROR_CODE_VALIDATION = "validation_error"
ERROR_CODE_DATA = "data_error"
ERROR_CODE_RESOURCE_NOT_FOUND = "resource_not_found"
ERROR_CODE_UNSUPPORTED_FILE_TYPE = "unsupported_file_type_error"
ERROR_CODE_CONVERSION = "conversion_error"
ERROR_CODE_OCR_ENGINE = "ocr_engine_error"
ERROR_CODE_TEXT_EXTRACTION = "text_extraction_error"
ERROR_CODE_BATCH_PROCESSING = "batch_processing_error"
ERROR_CODE_EXTERNAL_SERVICE = "external_service_error"
ERROR_CODE_PIPELINE = "pipeline_error"
ERROR_CODE_INTERNAL = "internal_error"

## ============================================================
## BASE EXCEPTION
## ============================================================
class OCRUniversalError(RuntimeError):
    """
        Base exception for the OCR Universal pipeline

        High-level workflow:
            1) Normalize OCR-specific failures
            2) Preserve structured context for debugging
            3) Support clean wrapping of lower-level exceptions

        Args:
            message: Human-readable error message
            error_code: Normalized application error code
            details: Optional structured context payload
            cause: Original exception if available
            is_retryable: Whether retry may succeed
    """

    def __init__(
        self,
        message: str,
        error_code: str = ERROR_CODE_INTERNAL,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        is_retryable: bool = False,
    ) -> None:
        ## Store normalized error metadata
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.is_retryable = is_retryable

        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the exception into a structured dictionary

            Returns:
                A normalized error payload
        """

        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "cause_type": self.cause.__class__.__name__
            if self.cause
            else None,
            "is_retryable": self.is_retryable,
        }

## ============================================================
## CUSTOM EXCEPTIONS
## ============================================================
class ConfigurationError(OCRUniversalError):
    """
        Raised when application configuration is invalid
    """

class ValidationError(OCRUniversalError):
    """
        Raised when request payload or parameters are invalid
    """

class DataError(OCRUniversalError):
    """
        Raised when input data, file content or output writing fails
    """

class ResourceNotFoundError(OCRUniversalError):
    """
        Raised when a required file or folder is missing
    """

class UnsupportedFileTypeError(OCRUniversalError):
    """
        Raised when an uploaded file extension is not supported
    """

class ConversionError(OCRUniversalError):
    """
        Raised when document conversion fails before OCR
    """

class OCREngineError(OCRUniversalError):
    """
        Raised when OCR engine initialization or execution fails
    """

class TextExtractionError(OCRUniversalError):
    """
        Raised when extracted text cannot be produced correctly
    """

class BatchProcessingError(OCRUniversalError):
    """
        Raised when batch or folder processing fails
    """

class ExternalServiceError(OCRUniversalError):
    """
        Raised when a remote OCR provider or external service fails
    """

class PipelineError(OCRUniversalError):
    """
        Raised when the OCR pipeline orchestration fails
    """

class UnknownOCRUniversalError(OCRUniversalError):
    """
        Raised when an unexpected exception must be normalized
    """

## ============================================================
## GENERIC HELPERS
## ============================================================
def raise_project_error(
    exc_type: Type[OCRUniversalError],
    message: str,
    *,
    error_code: str,
    details: Optional[Dict[str, Any]] = None,
    cause: Optional[Exception] = None,
    is_retryable: bool = False,
) -> None:
    """
        Log and raise a structured project exception

        High-level workflow:
            1) Build a normalized payload
            2) Attach original cause metadata when available
            3) Log the failure in a consistent format
            4) Raise the normalized project exception

        Args:
            exc_type: Exception class to raise
            message: Human-readable error message
            error_code: Normalized application error code
            details: Optional contextual details
            cause: Original exception if available
            is_retryable: Whether retry may succeed

        Raises:
            OCRUniversalError: Always
    """

    ## Build a normalized payload
    payload = details.copy() if details else {}

    ## Attach original cause metadata when available
    if cause is not None:
        payload["cause_message"] = str(cause)
        payload["cause_type"] = cause.__class__.__name__

    ## Emit a structured error log
    logger.error(
        "OCR Universal error | type=%s | code=%s | message=%s | "
        "retryable=%s | details=%s",
        exc_type.__name__,
        error_code,
        message,
        is_retryable,
        payload,
    )

    ## Raise the normalized project exception
    raise exc_type(
        message=message,
        error_code=error_code,
        details=payload,
        cause=cause,
        is_retryable=is_retryable,
    )

def wrap_exception(
    exc: Exception,
    *,
    exc_type: Type[OCRUniversalError],
    message: str,
    error_code: str,
    details: Optional[Dict[str, Any]] = None,
    is_retryable: bool = False,
) -> OCRUniversalError:
    """
        Wrap a raw exception into a structured project exception

        High-level workflow:
            1) Preserve the original exception
            2) Merge it into the structured payload
            3) Return a normalized project error instance

        Args:
            exc: Original exception
            exc_type: Target structured exception type
            message: Human-readable error message
            error_code: Normalized application error code
            details: Optional contextual details
            is_retryable: Whether retry may succeed

        Returns:
            A structured project exception instance
    """

    ## Start from existing details when provided
    payload = details.copy() if details else {}

    ## Attach original cause metadata
    payload["cause_message"] = str(exc)
    payload["cause_type"] = exc.__class__.__name__

    ## Return a normalized wrapped exception
    return exc_type(
        message=message,
        error_code=error_code,
        details=payload,
        cause=exc,
        is_retryable=is_retryable,
    )

def log_unhandled_exception(
    exc: Exception,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> UnknownOCRUniversalError:
    """
        Normalize an unexpected exception into a project-specific error

        Args:
            exc: Original unexpected exception
            context: Optional execution context

        Returns:
            A normalized unknown project exception
    """

    ## Build a safe payload from optional context
    payload = context.copy() if context else {}

    ## Attach original cause metadata
    payload["cause_message"] = str(exc)
    payload["cause_type"] = exc.__class__.__name__

    ## Log the unexpected failure
    logger.error(
        "Unhandled ocr-universal exception | type=%s | details=%s",
        exc.__class__.__name__,
        payload,
    )
    logger.debug("Unhandled traceback", exc_info=True)

    ## Return a normalized unknown project error
    return UnknownOCRUniversalError(
        message="An unexpected ocr-universal error occurred",
        error_code=ERROR_CODE_INTERNAL,
        details=payload,
        cause=exc,
        is_retryable=False,
    )

## ============================================================
## SPECIALIZED HELPERS
## ============================================================
def log_and_raise_missing_env(vars_missing: List[str]) -> None:
    """
        Log and raise a configuration error for missing environment variables

        Args:
            vars_missing: List of missing environment variable names

        Raises:
            ConfigurationError: Always
    """

    ## Build the explicit configuration error message
    message = (
        "Missing environment variables (placeholders detected): "
        + ", ".join(vars_missing)
    )

    ## Emit a direct configuration log
    logger.error(message)

    ## Raise the configuration error
    raise ConfigurationError(
        message=message,
        error_code=ERROR_CODE_CONFIGURATION,
        details={"missing_variables": vars_missing},
        is_retryable=False,
    )

def log_and_raise_missing_path(
    path: str | Path,
    *,
    resource_name: str = "Required resource",
) -> None:
    """
        Log and raise a missing resource error

        Args:
            path: Missing filesystem path
            resource_name: Human-readable resource label
    """

    ## Normalize path for payload stability
    normalized_path = str(Path(path))

    ## Raise structured missing resource error
    raise_project_error(
        exc_type=ResourceNotFoundError,
        message=f"{resource_name} not found",
        error_code=ERROR_CODE_RESOURCE_NOT_FOUND,
        details={"path": normalized_path},
        is_retryable=False,
    )

def log_and_raise_unsupported_file_type(
    file_name: str,
    extension: str,
) -> None:
    """
        Log and raise an unsupported file type error

        Args:
            file_name: Original input file name
            extension: Unsupported file extension
    """

    ## Build explicit unsupported type message
    message = (
        f"Unsupported file type for OCR processing: {file_name}"
    )

    ## Raise structured unsupported file type error
    raise_project_error(
        exc_type=UnsupportedFileTypeError,
        message=message,
        error_code=ERROR_CODE_UNSUPPORTED_FILE_TYPE,
        details={"file_name": file_name, "extension": extension},
        is_retryable=False,
    )

def log_and_raise_conversion_error(
    file_name: str,
    reason: str,
    *,
    cause: Optional[Exception] = None,
) -> None:
    """
        Log and raise a conversion error

        Args:
            file_name: File being converted
            reason: Human-readable failure reason
            cause: Original exception if available
    """

    ## Build conversion failure message
    message = f"Document conversion failed for file: {file_name}"

    ## Raise structured conversion error
    raise_project_error(
        exc_type=ConversionError,
        message=message,
        error_code=ERROR_CODE_CONVERSION,
        details={"file_name": file_name, "reason": reason},
        cause=cause,
        is_retryable=False,
    )

def log_and_raise_ocr_engine_error(
    engine_name: str,
    reason: str,
    *,
    cause: Optional[Exception] = None,
) -> None:
    """
        Log and raise an OCR engine error

        Args:
            engine_name: OCR engine identifier
            reason: Human-readable failure reason
            cause: Original exception if available
    """

    ## Build OCR engine failure message
    message = f"OCR engine failed: {engine_name}"

    ## Raise structured OCR engine error
    raise_project_error(
        exc_type=OCREngineError,
        message=message,
        error_code=ERROR_CODE_OCR_ENGINE,
        details={"engine_name": engine_name, "reason": reason},
        cause=cause,
        is_retryable=True,
    )

def log_and_raise_text_extraction_error(
    file_name: str,
    reason: str,
    *,
    cause: Optional[Exception] = None,
) -> None:
    """
        Log and raise a text extraction error

        Args:
            file_name: Input file name
            reason: Human-readable failure reason
            cause: Original exception if available
    """

    ## Build text extraction failure message
    message = f"Text extraction failed for file: {file_name}"

    ## Raise structured extraction error
    raise_project_error(
        exc_type=TextExtractionError,
        message=message,
        error_code=ERROR_CODE_TEXT_EXTRACTION,
        details={"file_name": file_name, "reason": reason},
        cause=cause,
        is_retryable=False,
    )

def log_and_raise_batch_processing_error(
    target: str,
    reason: str,
    *,
    cause: Optional[Exception] = None,
) -> None:
    """
        Log and raise a batch processing error

        Args:
            target: Batch target identifier
            reason: Human-readable failure reason
            cause: Original exception if available
    """

    ## Build batch failure message
    message = f"Batch processing failed for target: {target}"

    ## Raise structured batch error
    raise_project_error(
        exc_type=BatchProcessingError,
        message=message,
        error_code=ERROR_CODE_BATCH_PROCESSING,
        details={"target": target, "reason": reason},
        cause=cause,
        is_retryable=False,
    )

def log_and_raise_validation_error(
    message: str,
    *,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
        Log and raise a validation error

        Args:
            message: Human-readable validation error message
            details: Optional validation context
    """

    ## Raise structured validation error
    raise_project_error(
        exc_type=ValidationError,
        message=message,
        error_code=ERROR_CODE_VALIDATION,
        details=details,
        is_retryable=False,
    )

def log_and_raise_external_service_error(
    service_name: str,
    reason: str,
    *,
    cause: Optional[Exception] = None,
) -> None:
    """
        Log and raise an external service error

        Args:
            service_name: External service identifier
            reason: Human-readable failure reason
            cause: Original exception if available
    """

    ## Build external service failure message
    message = f"External OCR service failed: {service_name}"

    ## Raise structured external service error
    raise_project_error(
        exc_type=ExternalServiceError,
        message=message,
        error_code=ERROR_CODE_EXTERNAL_SERVICE,
        details={"service_name": service_name, "reason": reason},
        cause=cause,
        is_retryable=True,
    )

def log_and_raise_pipeline_error(
    step_name: str,
    reason: str,
    *,
    cause: Optional[Exception] = None,
) -> None:
    """
        Log and raise a pipeline error

        Args:
            step_name: Pipeline step name
            reason: Human-readable failure reason
            cause: Original exception if available
    """

    ## Build pipeline failure message
    message = f"Pipeline step failed [{step_name}]: {reason}"

    ## Raise structured pipeline error
    raise_project_error(
        exc_type=PipelineError,
        message=message,
        error_code=ERROR_CODE_PIPELINE,
        details={"step_name": step_name, "reason": reason},
        cause=cause,
        is_retryable=False,
    )