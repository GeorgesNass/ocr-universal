'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Dev"
__desc__ = "Pydantic schemas and typed data contracts for ocr-universal API, OCR jobs, batch processing, and exports."
'''

from __future__ import annotations

## STANDARD IMPORTS
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover
    BaseSettings = BaseModel  # type: ignore[misc, assignment]
    SettingsConfigDict = dict  # type: ignore[misc, assignment]

## ============================================================
## COMMON TYPES
## ============================================================
OcrEngineName = Literal[
    "tesseract",
    "easyocr",
    "paddleocr",
    "google_vision",
    "pdf2text",
    "beautifulsoup",
    "html2text",
    "striprtf",
]
InputKindName = Literal["image", "pdf", "office", "opendocument", "html", "folder"]
JobStatusName = Literal["pending", "running", "success", "failed", "cancelled"]
TaskTypeName = Literal[
    "detect_format",
    "convert_document",
    "extract_text",
    "export_text",
    "convert_batch",
    "convert_folder",
]
LogLevelName = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

## ============================================================
## BASE PYDANTIC SCHEMAS
## ============================================================
class BaseSchema(BaseModel):
    """
        Base schema with shared validation and serialization helpers

        Returns:
            A reusable Pydantic base model
    """

    model_config = {
        "extra": "forbid",
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }

    def to_dict(self) -> dict[str, Any]:
        """
            Convert the model to a Python dictionary

            Returns:
                Serialized model as dictionary
        """

        return self.model_dump()

    def to_json(self) -> str:
        """
            Convert the model to a JSON string

            Returns:
                Serialized model as JSON
        """

        return self.model_dump_json()

    def to_record(self) -> dict[str, Any]:
        """
            Convert the model to a row-oriented dictionary

            Returns:
                Flat dictionary representation
        """

        return self.model_dump(mode="json")

    def to_pandas(self) -> Any:
        """
            Convert the model to a one-row pandas DataFrame

            Returns:
                A pandas DataFrame with one row
        """

        import pandas as pd

        return pd.DataFrame([self.to_record()])

class WarningMixin(BaseSchema):
    """
        Mixin exposing warnings in response payloads

        Args:
            warnings: Warning messages list
    """

    warnings: list[str] = Field(default_factory=list)

## ============================================================
## SETTINGS AND DATACLASS CONFIGS
## ============================================================
class EnvSettings(BaseSettings):
    """
        Runtime settings for ocr-universal

        Args:
            app_name: Application name
            environment: Runtime environment
            default_ocr_engine: Default OCR engine
            batch_size: Default batch size
            max_workers: Max workers
            keep_converted_files: Whether converted files are kept
            output_extension: Default exported extension
    """

    model_config = SettingsConfigDict(
        extra="ignore",
        env_prefix="OCR_UNIVERSAL_",
        case_sensitive=False,
    )

    app_name: str = "ocr-universal"
    environment: str = "dev"
    default_ocr_engine: OcrEngineName = "tesseract"
    batch_size: int = Field(default=8, ge=1, le=1000)
    max_workers: int = Field(default=4, ge=1, le=256)
    keep_converted_files: bool = True
    output_extension: str = Field(default=".txt", min_length=1)

@dataclass(frozen=True)
class RuntimeConfig:
    """
        Runtime configuration

        Args:
            environment: Environment name
            log_level: Logging level
            batch_size: Batch size for multi-file processing
            max_workers: Maximum worker count
            request_timeout_seconds: External request timeout
            keep_converted_files: Whether temporary converted files are kept
            output_extension: Default text export extension
    """

    environment: str
    log_level: str
    batch_size: int
    max_workers: int
    request_timeout_seconds: int
    keep_converted_files: bool
    output_extension: str

    def to_dict(self) -> dict[str, Any]:
        """
            Convert the dataclass to a dictionary

            Returns:
                Serialized dataclass as dictionary
        """

        return asdict(self)

@dataclass(frozen=True)
class OcrConfig:
    """
        OCR engines and extraction flags

        Args:
            default_engine: Preferred OCR engine
            use_tesseract: Whether Tesseract OCR is enabled
            use_easyocr: Whether EasyOCR is enabled
            use_paddleocr: Whether PaddleOCR is enabled
            use_google_vision: Whether Google Vision OCR is enabled
            use_pdf2text: Whether PDF text extraction is enabled
            use_beautifulsoup: Whether BeautifulSoup HTML parsing is enabled
    """

    default_engine: str
    use_tesseract: bool
    use_easyocr: bool
    use_paddleocr: bool
    use_google_vision: bool
    use_pdf2text: bool
    use_beautifulsoup: bool

    def to_dict(self) -> dict[str, Any]:
        """
            Convert the dataclass to a dictionary

            Returns:
                Serialized dataclass as dictionary
        """

        return asdict(self)

@dataclass(frozen=True)
class PathConfig:
    """
        Path configuration

        Args:
            input_dir: Input directory
            converted_dir: Temporary converted directory
            output_dir: OCR text output directory
            logs_dir: Logs directory
    """

    input_dir: str
    converted_dir: str
    output_dir: str
    logs_dir: str

    def to_dict(self) -> dict[str, Any]:
        """
            Convert the dataclass to a dictionary

            Returns:
                Serialized dataclass as dictionary
        """

        return asdict(self)

## ============================================================
## COMMON OPERATIONAL SCHEMAS
## ============================================================
class HealthResponse(BaseSchema):
    """
        Healthcheck response schema

        Args:
            status: Service status
            service: Service name
            version: Application version
            timestamp: Response timestamp
    """

    status: str = "ok"
    service: str = "ocr-universal"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseSchema):
    """
        Standard API error schema

        Args:
            error: Normalized error code
            message: Human-readable message
            origin: Component where the error happened
            details: Diagnostic details
            request_id: Optional request correlation id
    """

    error: str
    message: str
    origin: str = "unknown"
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str = "n/a"

class StatusResponse(BaseSchema):
    """
        Generic status response schema

        Args:
            status: Current status
            message: Optional message
            progress: Optional progress value
            metadata: Optional metadata payload
    """

    status: str
    message: str = ""
    progress: float | None = Field(default=None, ge=0.0, le=100.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

class StructuredLogEvent(BaseSchema):
    """
        Structured log schema

        Args:
            level: Log level
            event: Event name
            message: Human-readable message
            logger_name: Logger name
            context: Additional context
            timestamp: Event timestamp
    """

    level: LogLevelName
    event: str
    message: str
    logger_name: str = "ocr-universal"
    context: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MetricPoint(BaseSchema):
    """
        Monitoring metric schema

        Args:
            name: Metric name
            value: Metric value
            unit: Optional metric unit
            tags: Optional metric tags
    """

    name: str
    value: float
    unit: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)

class MonitoringResponse(WarningMixin):
    """
        Monitoring response schema

        Args:
            metrics: Metric points list
            summary: Aggregated summary
    """

    metrics: list[MetricPoint] = Field(default_factory=list)
    summary: dict[str, float] = Field(default_factory=dict)

## ============================================================
## CORE OCR CONTRACTS
## ============================================================
class OcrEngineConfigSchema(BaseSchema):
    """
        OCR engine configuration schema

        Args:
            engine: OCR engine name
            language: Optional OCR language code
            dpi: Optional DPI for rasterization
            preserve_layout: Whether layout should be preserved
    """

    engine: OcrEngineName = "tesseract"
    language: str | None = None
    dpi: int | None = Field(default=None, ge=72, le=1200)
    preserve_layout: bool = False

class FileDescriptor(BaseSchema):
    """
        File descriptor schema

        Args:
            file_name: Original file name
            input_kind: Detected input kind
            mime_type: MIME type if available
            size_bytes: File size in bytes
    """

    file_name: str
    input_kind: InputKindName
    mime_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)

class OcrTextArtifact(BaseSchema):
    """
        OCR text artifact schema

        Args:
            file_name: Original file name
            output_file_name: Exported text file name
            extracted_text: Extracted text content
            output_path: Optional output path
    """

    file_name: str
    output_file_name: str
    extracted_text: str
    output_path: str | None = None

class ConvertRequest(BaseSchema):
    """
        Single-file convert request schema

        Args:
            engine: OCR engine name
            save_output: Whether output text file is persisted
            return_text: Whether extracted text is returned in response
    """

    engine: OcrEngineName = "tesseract"
    save_output: bool = True
    return_text: bool = True

class ConvertResponse(WarningMixin):
    """
        Single-file convert response schema

        Args:
            status: Operation status
            file: Input file descriptor
            engine: OCR engine used
            artifact: OCR text artifact
            metadata: Additional metadata
    """

    status: JobStatusName
    file: FileDescriptor
    engine: OcrEngineName
    artifact: OcrTextArtifact
    metadata: dict[str, Any] = Field(default_factory=dict)

class ConvertBatchRequest(BaseSchema):
    """
        Batch convert request schema

        Args:
            engine: OCR engine name
            save_output: Whether output text files are persisted
            return_text: Whether extracted texts are returned in response
            stop_on_error: Whether batch stops on first error
    """

    engine: OcrEngineName = "tesseract"
    save_output: bool = True
    return_text: bool = False
    stop_on_error: bool = False

class ConvertBatchItem(BaseSchema):
    """
        Batch convert item schema

        Args:
            status: Item status
            file_name: Input file name
            engine: OCR engine used
            extracted_text: Optional extracted text
            output_path: Optional output path
            error: Optional item error
    """

    status: JobStatusName
    file_name: str
    engine: OcrEngineName
    extracted_text: str | None = None
    output_path: str | None = None
    error: str | None = None

class ConvertBatchResponse(WarningMixin):
    """
        Batch convert response schema

        Args:
            status: Operation status
            items: Batch items
            processed_count: Processed file count
            success_count: Success file count
            failed_count: Failed file count
    """

    status: JobStatusName
    items: list[ConvertBatchItem] = Field(default_factory=list)
    processed_count: int = Field(..., ge=0)
    success_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)

    @model_validator(mode="after")
    def validate_counts(self) -> "ConvertBatchResponse":
        """
            Validate batch count consistency

            Returns:
                The validated batch response
        """

        if self.processed_count != len(self.items):
            raise ValueError("processed_count must match len(items)")
        if self.success_count + self.failed_count != self.processed_count:
            raise ValueError(
                "success_count + failed_count must match processed_count"
            )
        return self

class ConvertFolderRequest(BaseSchema):
    """
        Folder convert request schema

        Args:
            folder_path: Server folder path
            engine: OCR engine name
            recursive: Whether subfolders are traversed
            save_output: Whether output files are persisted
            return_text: Whether extracted texts are returned
    """

    folder_path: str
    engine: OcrEngineName = "tesseract"
    recursive: bool = True
    save_output: bool = True
    return_text: bool = False

class ConvertFolderResponse(ConvertBatchResponse):
    """
        Folder convert response schema

        Args:
            status: Operation status
            items: Batch items
            processed_count: Processed file count
            success_count: Success file count
            failed_count: Failed file count
            folder_path: Processed folder path
    """

    folder_path: str

## ============================================================
## DATASET AND PIPELINE SCHEMAS
## ============================================================
class DatasetRecord(BaseSchema):
    """
        Generic OCR dataset record schema

        Args:
            record_id: Record identifier
            payload: Raw payload content
            metadata: Optional metadata
    """

    record_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DatasetInput(BaseSchema):
    """
        Dataset input schema

        Args:
            name: Dataset name
            records: Dataset records
    """

    name: str
    records: list[DatasetRecord]

    @field_validator("records")
    @classmethod
    def validate_records(cls, value: list[DatasetRecord]) -> list[DatasetRecord]:
        """
            Validate dataset records list

            Args:
                value: Candidate dataset records

            Returns:
                The validated records list
        """

        if not value:
            raise ValueError("records must contain at least one item")
        return value

class DatasetOutput(BaseSchema):
    """
        Dataset output schema

        Args:
            name: Dataset name
            row_count: Number of rows
            artifacts: Generated artifacts
    """

    name: str
    row_count: int = Field(..., ge=0)
    artifacts: list[str] = Field(default_factory=list)

class PipelineTask(BaseSchema):
    """
        Pipeline task schema

        Args:
            task_id: Task identifier
            task_type: Task type
            status: Task status
            progress: Task progress percentage
            input_payload: Task input payload
            output_payload: Task output payload
    """

    task_id: str
    task_type: TaskTypeName
    status: JobStatusName = "pending"
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)

class PipelineJob(BaseSchema):
    """
        Pipeline job schema

        Args:
            job_id: Job identifier
            status: Job status
            tasks: Job tasks
            progress: Job progress percentage
            metadata: Job metadata
    """

    job_id: str
    status: JobStatusName = "pending"
    tasks: list[PipelineTask] = Field(default_factory=list)
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_progress(self) -> "PipelineJob":
        """
            Validate progress consistency

            Returns:
                The validated pipeline job
        """

        if self.tasks and self.progress < min(task.progress for task in self.tasks):
            raise ValueError("job progress cannot be below the minimum task progress")
        return self