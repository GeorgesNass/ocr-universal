'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Dev"
__desc__ = "Unified configuration loader for ocr-universal: dotenv, env parsing, paths, OCR engines, extraction flags, LibreOffice, secrets and runtime metadata."
'''

from __future__ import annotations

import json
import os
import platform
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Tuple

from src.core.errors import ConfigurationError
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

## ============================================================
## PLACEHOLDER TOKENS
## ============================================================
PLACEHOLDER_PREFIXES: Tuple[str, ...] = ("<YOUR_", "YOUR_", "CHANGE_ME", "REPLACE_ME", "TODO")

## ============================================================
## OS / SYSTEM CONSTANTS
## ============================================================
SYSTEM_NAME = platform.system().lower()
IS_WINDOWS = SYSTEM_NAME == "windows"
IS_LINUX = SYSTEM_NAME == "linux"
IS_MACOS = SYSTEM_NAME == "darwin"
DEFAULT_ENCODING = "utf-8"
DEFAULT_CSV_SEPARATOR = "\t"
DEFAULT_CSV_EXTENSION = ".txt"
DEFAULT_PYTHON_ENV = "python3.10" if IS_LINUX else "python"

## ============================================================
## STABLE DOMAIN CONSTANTS
## ============================================================
DEFAULT_APP_NAME = "ocr-universal"
DEFAULT_APP_VERSION = "1.0.0"
DEFAULT_ENVIRONMENT = "dev"
DEFAULT_PROFILE = "cpu"

DEFAULT_DATA_DIR = "data"
DEFAULT_LOGS_DIR = "logs"
DEFAULT_ARTIFACTS_DIR = "artifacts"
DEFAULT_SECRETS_DIR = "secrets"

DEFAULT_INPUT_DIR = "data/input"
DEFAULT_CONVERTED_DIR = "data/converted"
DEFAULT_OUTPUT_DIR = "data/output"
DEFAULT_EXPORTS_DIR = "artifacts/exports"
DEFAULT_REPORTS_DIR = "artifacts/reports"
DEFAULT_TMP_DIR = "data/tmp"

DEFAULT_MAX_PDF_SIZE_MB = 50
DEFAULT_BATCH_SIZE = 8
DEFAULT_MAX_WORKERS = 4
DEFAULT_REQUEST_TIMEOUT_SECONDS = 120

DEFAULT_WINDOWS_LIBREOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"
DEFAULT_LINUX_LIBREOFFICE = "/usr/bin/libreoffice"
DEFAULT_OTHER_LIBREOFFICE = "soffice"

SUPPORTED_OCR_ENGINES = ("tesseract", "easyocr", "paddleocr", "google_vision")
ALLOWED_EXTENSIONS: Tuple[str, ...] = (
    ".html", ".htm", ".mht", ".odt", ".rtf", ".docx", ".doc", ".pptx", ".ppt",
    ".txt", ".pdf", ".png", ".jpg", ".jpeg", ".svg", ".tif", ".tiff", ".bitmap",
    ".bmp", ".gif", ".jfif", ".webp", ".xls", ".xlsx",
)
ENCODINGS_TO_TRY: Tuple[str, ...] = (
    "utf-8", "utf-8-sig", "latin-1", "windows-1252", "iso8859-1", "iso8859-15",
    "mac_roman", "cp850", "cp1250", "cp1254", "ascii", "big5", "shift_jis",
    "euc-jp", "gb18030",
)

## ============================================================
## CONFIG MODELS
## ============================================================
@dataclass(frozen=True)
class ExecutionMetadata:
    """
        Execution metadata

        Args:
            run_id: Unique runtime identifier
            started_at_utc: UTC timestamp when config was built
            hostname: Current host name
            platform_name: Current operating system name
            profile: Active runtime profile
            environment: Active environment
    """

    run_id: str
    started_at_utc: str
    hostname: str
    platform_name: str
    profile: str
    environment: str

@dataclass(frozen=True)
class PathsConfig:
    """
        Filesystem paths configuration

        Args:
            project_root: Project root directory
            src_dir: Source directory
            data_dir: Main data directory
            input_dir: Input file directory
            converted_dir: Converted file directory
            output_dir: OCR output directory
            tmp_dir: Temporary working directory
            artifacts_dir: Artifacts root directory
            exports_dir: Exports directory
            reports_dir: Reports directory
            logs_dir: Logs directory
            secrets_dir: Secrets directory
            libreoffice_binary: LibreOffice binary path
    """

    project_root: Path
    src_dir: Path
    data_dir: Path
    input_dir: Path
    converted_dir: Path
    output_dir: Path
    tmp_dir: Path
    artifacts_dir: Path
    exports_dir: Path
    reports_dir: Path
    logs_dir: Path
    secrets_dir: Path
    libreoffice_binary: Path

@dataclass(frozen=True)
class RuntimeConfig:
    """
        Runtime configuration

        Args:
            environment: Environment name
            profile: Active runtime profile
            debug: Whether debug mode is enabled
            log_level: Logging level
            python_env: Preferred python executable name
            batch_size: Batch size for multi-file processing
            max_workers: Maximum worker count
            request_timeout_seconds: External request timeout
            prune_after_process: Whether processed temporary files are deleted
            max_pdf_size_mb: Maximum accepted PDF size in megabytes
            csv_separator: Output CSV separator
            csv_extension: Default text export extension
            allowed_origins: Allowed origins for future API usage
    """

    environment: str
    profile: str
    debug: bool
    log_level: str
    python_env: str
    batch_size: int
    max_workers: int
    request_timeout_seconds: int
    prune_after_process: bool
    max_pdf_size_mb: int
    csv_separator: str
    csv_extension: str
    allowed_origins: list[str]

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
            use_tika: Whether Apache Tika extraction is enabled
            use_pypdf2: Whether PyPDF2 extraction is enabled
            use_pdftotext: Whether pdftotext extraction is enabled
            use_pdf2image: Whether PDF to image conversion is enabled
            use_beautifulsoup: Whether BeautifulSoup HTML parsing is enabled
            use_html2text: Whether html2text parsing is enabled
            use_urllib: Whether urllib fetching/parsing is enabled
            include_docx_headers: Whether DOCX headers are included
            include_docx_tables: Whether DOCX tables are included
            use_detailed_excel_extraction: Whether detailed Excel extraction is enabled
            use_detailed_pptx_extraction: Whether detailed PPTX extraction is enabled
    """

    default_engine: str
    use_tesseract: bool
    use_easyocr: bool
    use_paddleocr: bool
    use_google_vision: bool
    use_tika: bool
    use_pypdf2: bool
    use_pdftotext: bool
    use_pdf2image: bool
    use_beautifulsoup: bool
    use_html2text: bool
    use_urllib: bool
    include_docx_headers: bool
    include_docx_tables: bool
    use_detailed_excel_extraction: bool
    use_detailed_pptx_extraction: bool

@dataclass(frozen=True)
class FormatConfig:
    """
        File format and encoding configuration

        Args:
            allowed_extensions: Supported file extensions
            encodings_to_try: Candidate encodings for text decoding
    """

    allowed_extensions: tuple[str, ...] = field(default_factory=lambda: ALLOWED_EXTENSIONS)
    encodings_to_try: tuple[str, ...] = field(default_factory=lambda: ENCODINGS_TO_TRY)

@dataclass(frozen=True)
class SecretsConfig:
    """
        Secret values resolved from env or files

        Args:
            google_application_credentials: Optional Google service account path or content
            google_vision_api_key: Optional Google Vision API key
            api_key: Optional generic API key
    """

    google_application_credentials: str
    google_vision_api_key: str
    api_key: str

@dataclass(frozen=True)
class AppConfig:
    """
        Unified application configuration

        Args:
            app_name: Application name
            app_version: Application version
            execution: Execution metadata
            paths: Filesystem paths configuration
            runtime: Runtime configuration
            ocr: OCR engines and extraction flags
            formats: File format and encoding configuration
            secrets: Secret values
            extra: Additional metadata
    """

    app_name: str
    app_version: str
    execution: ExecutionMetadata
    paths: PathsConfig
    runtime: RuntimeConfig
    ocr: OcrConfig
    formats: FormatConfig
    secrets: SecretsConfig
    extra: dict[str, Any] = field(default_factory=dict)

## ============================================================
## DOTENV / ENV HELPERS
## ============================================================
def _resolve_project_root() -> Path:
    """
        Resolve the project root directory

        High-level workflow:
            1) Prefer PROJECT_ROOT when explicitly provided
            2) Otherwise derive the root from this file location

        Args:
            None

        Returns:
            Absolute project root path
    """

    ## Prefer explicit project root override when available
    project_root_raw = os.getenv("PROJECT_ROOT", "").strip()
    return Path(project_root_raw).expanduser().resolve() if project_root_raw else Path(__file__).resolve().parents[2]

def _load_dotenv_if_present() -> None:
    """
        Load a local .env file if available

        Args:
            None

        Returns:
            None
    """

    ## Import dotenv lazily to avoid hard dependency issues
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    ## Load project-level .env when present
    env_path = _resolve_project_root() / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)

def _is_placeholder(value: str) -> bool:
    """
        Detect placeholder-like values

        Args:
            value: Raw environment value

        Returns:
            True if the value looks like a placeholder
    """

    ## Normalize before inspection
    normalized = value.strip().upper()
    return any(token in normalized for token in PLACEHOLDER_PREFIXES)

def _get_env(name: str, default: Optional[str] = None) -> str:
    """
        Read environment variable safely

        Args:
            name: Environment variable name
            default: Optional default value

        Returns:
            Normalized environment value

        Raises:
            ConfigurationError: If missing and no default provided
    """

    ## Read raw value from environment
    value = os.getenv(name)
    if value is None:
        if default is None:
            raise ConfigurationError(f"Missing environment variable: {name}")
        return default
    return value.strip()

def _get_env_bool(name: str, default: bool) -> bool:
    """
        Parse a boolean environment variable

        Args:
            name: Environment variable name
            default: Default fallback value

        Returns:
            Parsed boolean value
    """

    ## Parse normalized boolean values
    raw = _get_env(name, str(default)).lower()
    if raw in {"true", "1", "yes", "y", "on"}:
        return True
    if raw in {"false", "0", "no", "n", "off"}:
        return False
    raise ConfigurationError(f"Invalid boolean value for {name}: {raw}")
    
def _get_env_int(name: str, default: int) -> int:
    """
        Parse an integer environment variable

        Args:
            name: Environment variable name
            default: Default fallback value

        Returns:
            Parsed integer value
    """

    ## Parse integer strictly
    try:
        return int(_get_env(name, str(default)))
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc

def _get_env_list(name: str, default: Optional[list[str]] = None, *, separator: str = ",") -> list[str]:
    """
        Parse a list-like environment variable

        Args:
            name: Environment variable name
            default: Default fallback list
            separator: Value separator

        Returns:
            Parsed list of strings
    """

    ## Read raw list value
    raw = _get_env(name, "")
    if not raw:
        return list(default or [])
    return [item.strip() for item in raw.split(separator) if item.strip()]

def _expand_env_vars(value: str) -> str:
    """
        Expand shell variables and user home in a string

        Args:
            value: Raw string value

        Returns:
            Expanded string
    """

    ## Expand shell variables and user home
    return os.path.expandvars(value)

def _resolve_path(path_value: str, project_root: Path) -> Path:
    """
        Resolve a path against the project root

        Args:
            path_value: Raw path value
            project_root: Project root directory

        Returns:
            Resolved absolute path
    """

    ## Expand shell variables and user home
    path_obj = Path(_expand_env_vars(path_value)).expanduser()
    return path_obj.resolve() if path_obj.is_absolute() else (project_root / path_obj).resolve()

def _read_secret_value(direct_key: str, file_key: str, *, project_root: Path, default: str = "") -> str:
    """
        Read a secret from env directly or from a file path

        High-level workflow:
            1) Prefer direct env value
            2) Fallback to secret file path
            3) Return default when nothing is available

        Args:
            direct_key: Environment variable containing the secret
            file_key: Environment variable containing the secret file path
            project_root: Project root directory
            default: Default fallback value

        Returns:
            Secret value or default
    """

    ## Prefer direct env secret value first
    direct_value = _get_env(direct_key, default)
    if direct_value and not _is_placeholder(direct_value):
        return direct_value

    ## Fallback to file-based secret
    secret_file_raw = _get_env(file_key, "")
    if not secret_file_raw:
        return default

    ## Resolve and read secret file when available
    secret_file = _resolve_path(secret_file_raw, project_root)
    if secret_file.exists() and secret_file.is_file():
        return secret_file.read_text(encoding=DEFAULT_ENCODING).strip()
    return default

## ============================================================
## PROFILE HELPERS
## ============================================================
def _get_profiled_env(name: str, default: str, profile: str) -> str:
    """
        Read an env value with optional profile override

        Args:
            name: Base environment variable name
            default: Default fallback value
            profile: Active runtime profile

        Returns:
            Resolved string value
    """

    ## Prefer CPU_/GPU_ override when present
    override_key = f"{profile.upper()}_{name}"
    return _get_env(override_key, default) if os.getenv(override_key) is not None else _get_env(name, default)

def _get_profiled_env_bool(name: str, default: bool, profile: str) -> bool:
    """
        Read a boolean env value with optional profile override

        Args:
            name: Base environment variable name
            default: Default fallback value
            profile: Active runtime profile

        Returns:
            Parsed boolean value
    """

    ## Prefer CPU_/GPU_ override when present
    override_key = f"{profile.upper()}_{name}"
    return _get_env_bool(override_key, default) if os.getenv(override_key) is not None else _get_env_bool(name, default)

def _get_profiled_env_int(name: str, default: int, profile: str) -> int:
    """
        Read an integer env value with optional profile override

        Args:
            name: Base environment variable name
            default: Default fallback value
            profile: Active runtime profile

        Returns:
            Parsed integer value
    """

    ## Prefer CPU_/GPU_ override when present
    override_key = f"{profile.upper()}_{name}"
    return _get_env_int(override_key, default) if os.getenv(override_key) is not None else _get_env_int(name, default)

## ============================================================
## VALIDATION / BUILD HELPERS
## ============================================================
def _resolve_libreoffice_binary() -> Path:
    """
        Resolve the LibreOffice executable path

        High-level workflow:
            1) Prefer PATH_LIBRE_OFFICE from environment
            2) Otherwise use an OS-aware default path

        Args:
            None

        Returns:
            Resolved LibreOffice binary path
    """

    ## Choose the default executable depending on OS
    if IS_WINDOWS:
        default_value = DEFAULT_WINDOWS_LIBREOFFICE
    elif IS_LINUX:
        default_value = DEFAULT_LINUX_LIBREOFFICE
    else:
        default_value = DEFAULT_OTHER_LIBREOFFICE

    ## Resolve the binary path
    return Path(_expand_env_vars(_get_env("PATH_LIBRE_OFFICE", default_value))).expanduser()

def _validate_required_placeholders(keys: list[str]) -> None:
    """
        Validate that required env keys are not unresolved placeholders

        Args:
            keys: Environment keys to inspect

        Returns:
            None
    """

    ## Collect invalid placeholder values
    invalid_keys = [key for key in keys if (value := _get_env(key, "")) and _is_placeholder(value)]
    if invalid_keys:
        raise ConfigurationError("Placeholder values detected for: " + ", ".join(invalid_keys))

def _validate_positive_int(value: int, field_name: str) -> None:
    """
        Validate that an integer is strictly positive

        Args:
            value: Integer value
            field_name: Human-readable field name

        Returns:
            None
    """

    ## Reject non-positive integers
    if value <= 0:
        raise ConfigurationError(f"{field_name} must be > 0. Got: {value}")

def _validate_engine(value: str) -> str:
    """
        Validate the default OCR engine

        Args:
            value: Raw OCR engine name

        Returns:
            Validated OCR engine name
    """

    ## Restrict engines to supported values
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_OCR_ENGINES:
        raise ConfigurationError(f"DEFAULT_OCR_ENGINE must be one of: {', '.join(SUPPORTED_OCR_ENGINES)}")
    return normalized

def _ensure_directories_exist(paths: list[Path]) -> None:
    """
        Ensure runtime directories exist

        Args:
            paths: Directories to create if missing

        Returns:
            None
    """

    ## Create runtime directories safely
    for directory in paths:
        directory.mkdir(parents=True, exist_ok=True)

def _validate_config(config: AppConfig) -> None:
    """
        Validate the final structured configuration

        High-level workflow:
            1) Validate runtime numeric values
            2) Validate OCR engine consistency
            3) Validate file format collections

        Args:
            config: Structured configuration object

        Returns:
            None
    """

    ## Validate runtime numeric values
    _validate_positive_int(config.runtime.batch_size, "BATCH_SIZE")
    _validate_positive_int(config.runtime.max_workers, "MAX_WORKERS")
    _validate_positive_int(config.runtime.request_timeout_seconds, "REQUEST_TIMEOUT_SECONDS")
    _validate_positive_int(config.runtime.max_pdf_size_mb, "MAX_PDF_SIZE_MB")

    ## Validate OCR engine consistency
    if config.ocr.default_engine == "tesseract" and not config.ocr.use_tesseract:
        raise ConfigurationError("DEFAULT_OCR_ENGINE=tesseract but USE_TESSERACT is disabled")
    if config.ocr.default_engine == "easyocr" and not config.ocr.use_easyocr:
        raise ConfigurationError("DEFAULT_OCR_ENGINE=easyocr but USE_EASYOCR is disabled")
    if config.ocr.default_engine == "paddleocr" and not config.ocr.use_paddleocr:
        raise ConfigurationError("DEFAULT_OCR_ENGINE=paddleocr but USE_PADDLEOCR is disabled")
    if config.ocr.default_engine == "google_vision" and not config.ocr.use_google_vision:
        raise ConfigurationError("DEFAULT_OCR_ENGINE=google_vision but USE_GOOGLE_VISION is disabled")

    ## Validate format collections
    if not config.formats.allowed_extensions:
        raise ConfigurationError("ALLOWED_EXTENSIONS cannot be empty")
    if not config.formats.encodings_to_try:
        raise ConfigurationError("ENCODINGS_TO_TRY cannot be empty")

## ============================================================
## EXPORT HELPERS
## ============================================================
def config_to_dict(config: AppConfig) -> dict[str, Any]:
    """
        Convert AppConfig into a serializable dictionary

        Args:
            config: Structured configuration object

        Returns:
            Dictionary representation
    """

    ## Convert dataclass tree into a plain dictionary
    payload = asdict(config)

    ## Normalize Path objects recursively
    def _normalize(value: Any) -> Any:
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, dict):
            return {key: _normalize(val) for key, val in value.items()}
        if isinstance(value, list):
            return [_normalize(item) for item in value]
        return value

    return _normalize(payload)

def config_to_json(config: AppConfig) -> str:
    """
        Convert AppConfig into a JSON string

        Args:
            config: Structured configuration object

        Returns:
            JSON string
    """

    ## Serialize normalized configuration
    return json.dumps(config_to_dict(config), indent=2, ensure_ascii=False)

## ============================================================
## APP FACTORY
## ============================================================
@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """
        Build full application configuration from environment variables

        High-level workflow:
            1) Load optional local .env
            2) Resolve root paths and runtime profile
            3) Build runtime, OCR, formats and secret sections
            4) Validate and cache final configuration

        Args:
            None

        Returns:
            AppConfig instance
    """

    ## Load optional local .env file first
    _load_dotenv_if_present()

    ## Resolve project root and runtime profile
    project_root = _resolve_project_root()
    environment = _get_env("ENVIRONMENT", DEFAULT_ENVIRONMENT).lower()
    profile = _get_env("PROFILE", DEFAULT_PROFILE).lower()

    ## Validate placeholder values where relevant
    _validate_required_placeholders(["ENVIRONMENT", "PROFILE", "GOOGLE_VISION_API_KEY", "API_KEY"])

    ## Build execution metadata
    execution = ExecutionMetadata(
        run_id=_get_env("RUN_ID", str(uuid.uuid4())),
        started_at_utc=datetime.now(timezone.utc).isoformat(),
        hostname=platform.node(),
        platform_name=SYSTEM_NAME,
        profile=profile,
        environment=environment,
    )

    ## Resolve filesystem paths
    paths = PathsConfig(
        project_root=project_root, src_dir=(project_root / "src").resolve(),
        data_dir=_resolve_path(_get_env("DATA_DIR", DEFAULT_DATA_DIR), project_root),
        input_dir=_resolve_path(_get_env("INPUT_DIR", DEFAULT_INPUT_DIR), project_root),
        converted_dir=_resolve_path(_get_env("CONVERTED_DIR", DEFAULT_CONVERTED_DIR), project_root),
        output_dir=_resolve_path(_get_env("OUTPUT_DIR", DEFAULT_OUTPUT_DIR), project_root),
        tmp_dir=_resolve_path(_get_env("TMP_DIR", DEFAULT_TMP_DIR), project_root),
        artifacts_dir=_resolve_path(_get_env("ARTIFACTS_DIR", DEFAULT_ARTIFACTS_DIR), project_root),
        exports_dir=_resolve_path(_get_env("EXPORTS_DIR", DEFAULT_EXPORTS_DIR), project_root),
        reports_dir=_resolve_path(_get_env("REPORTS_DIR", DEFAULT_REPORTS_DIR), project_root),
        logs_dir=_resolve_path(_get_env("LOGS_DIR", DEFAULT_LOGS_DIR), project_root),
        secrets_dir=_resolve_path(_get_env("SECRETS_DIR", DEFAULT_SECRETS_DIR), project_root),
        libreoffice_binary=_resolve_libreoffice_binary(),
    )

    ## Ensure runtime directories exist
    _ensure_directories_exist([
        paths.data_dir, paths.input_dir, paths.converted_dir, paths.output_dir, paths.tmp_dir,
        paths.artifacts_dir, paths.exports_dir, paths.reports_dir, paths.logs_dir, paths.secrets_dir,
    ])

    ## Build runtime section
    runtime = RuntimeConfig(
        environment=environment, profile=profile,
        debug=_get_profiled_env_bool("DEBUG", environment == "dev", profile),
        log_level=_get_profiled_env("LOG_LEVEL", "INFO", profile),
        python_env=_get_profiled_env("PYTHON_ENV", DEFAULT_PYTHON_ENV, profile),
        batch_size=_get_profiled_env_int("BATCH_SIZE", DEFAULT_BATCH_SIZE, profile),
        max_workers=_get_profiled_env_int("MAX_WORKERS", DEFAULT_MAX_WORKERS, profile),
        request_timeout_seconds=_get_profiled_env_int("REQUEST_TIMEOUT_SECONDS", DEFAULT_REQUEST_TIMEOUT_SECONDS, profile),
        prune_after_process=_get_profiled_env_bool("PRUNE_AFTER_PROCESS", True, profile),
        max_pdf_size_mb=_get_profiled_env_int("MAX_PDF_SIZE_MB", DEFAULT_MAX_PDF_SIZE_MB, profile),
        csv_separator=_get_env("CSV_SEPARATOR", DEFAULT_CSV_SEPARATOR),
        csv_extension=_get_env("CSV_EXTENSION", DEFAULT_CSV_EXTENSION),
        allowed_origins=_get_env_list("ALLOWED_ORIGINS", ["*"]),
    )

    ## Build OCR section
    ocr = OcrConfig(
        default_engine=_validate_engine(_get_env("DEFAULT_OCR_ENGINE", "tesseract")),
        use_tesseract=_get_env_bool("USE_TESSERACT", True),
        use_easyocr=_get_env_bool("USE_EASYOCR", False),
        use_paddleocr=_get_env_bool("USE_PADDLEOCR", False),
        use_google_vision=_get_env_bool("USE_GOOGLE_VISION", False),
        use_tika=_get_env_bool("USE_TIKA", True),
        use_pypdf2=_get_env_bool("USE_PYPDF2", True),
        use_pdftotext=_get_env_bool("USE_PDFTOTEXT", True),
        use_pdf2image=_get_env_bool("USE_PDF2IMAGE", True),
        use_beautifulsoup=_get_env_bool("USE_BEAUTIFULSOUP", True),
        use_html2text=_get_env_bool("USE_HTML2TEXT", False),
        use_urllib=_get_env_bool("USE_URLLIB", False),
        include_docx_headers=_get_env_bool("INCLUDE_DOCX_HEADERS", True),
        include_docx_tables=_get_env_bool("INCLUDE_DOCX_TABLES", True),
        use_detailed_excel_extraction=_get_env_bool("USE_DETAILED_EXCEL_EXTRACTION", False),
        use_detailed_pptx_extraction=_get_env_bool("USE_DETAILED_PPTX_EXTRACTION", False),
    )

    ## Build formats section
    formats = FormatConfig()

    ## Resolve optional secrets
    secrets = SecretsConfig(
        google_application_credentials=_read_secret_value(
            "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_APPLICATION_CREDENTIALS_FILE", project_root=project_root,
        ),
        google_vision_api_key=_read_secret_value(
            "GOOGLE_VISION_API_KEY", "GOOGLE_VISION_API_KEY_FILE", project_root=project_root,
        ),
        api_key=_read_secret_value("API_KEY", "API_KEY_FILE", project_root=project_root),
    )

    ## Build final config
    config = AppConfig(
        app_name=_get_env("APP_NAME", DEFAULT_APP_NAME), app_version=_get_env("APP_VERSION", DEFAULT_APP_VERSION),
        execution=execution, paths=paths, runtime=runtime, ocr=ocr, formats=formats, secrets=secrets,
        extra={
            "system_name": SYSTEM_NAME, "is_windows": IS_WINDOWS, "is_linux": IS_LINUX, "is_macos": IS_MACOS,
            "supported_ocr_engines": list(SUPPORTED_OCR_ENGINES),
        },
    )

    ## Validate final configuration
    _validate_config(config)

    ## Log concise configuration summary
    logger.info(
        "Configuration loaded | app=%s | env=%s | profile=%s | engine=%s | input_dir=%s | output_dir=%s | run_id=%s",
        config.app_name, config.runtime.environment, config.runtime.profile, config.ocr.default_engine,
        config.paths.input_dir, config.paths.output_dir, config.execution.run_id,
    )
    
    return config

def load_config() -> AppConfig:
    """
        Backward-compatible alias for configuration loading

        Args:
            None

        Returns:
            AppConfig instance
    """

    ## Keep compatibility with existing imports
    return get_config()

def build_config() -> AppConfig:
    """
        Backward-compatible config builder

        Args:
            None

        Returns:
            AppConfig instance
    """

    ## Preserve the original public entrypoint
    return get_config()

## ============================================================
## PUBLIC SINGLETON CONFIG
## ============================================================
CONFIG: AppConfig = get_config()
config = CONFIG