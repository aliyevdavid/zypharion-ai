from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class ExtractionCategory(StrEnum):
    """Browser observation category affected by a localized failure."""

    METADATA = "metadata"
    HEADINGS = "headings"
    LINKS = "links"
    IMAGES = "images"
    FORMS = "forms"
    BUTTONS = "buttons"
    INPUTS = "inputs"
    CONSOLE = "console"
    METRICS = "metrics"


class ExtractionWarningCode(StrEnum):
    """Stable codes for localized browser extraction failures."""

    METADATA_EXTRACTION_FAILED = "metadata_extraction_failed"
    HEADINGS_EXTRACTION_FAILED = "headings_extraction_failed"
    LINKS_EXTRACTION_FAILED = "links_extraction_failed"
    IMAGES_EXTRACTION_FAILED = "images_extraction_failed"
    FORMS_EXTRACTION_FAILED = "forms_extraction_failed"
    BUTTONS_EXTRACTION_FAILED = "buttons_extraction_failed"
    INPUTS_EXTRACTION_FAILED = "inputs_extraction_failed"
    CONSOLE_EXTRACTION_FAILED = "console_extraction_failed"
    METRICS_EXTRACTION_FAILED = "metrics_extraction_failed"


class ExtractionWarning(BaseModel):
    """Safe details about one unavailable browser observation category."""

    category: ExtractionCategory
    code: ExtractionWarningCode
    message: str = Field(min_length=1)


class HeadingInfo(BaseModel):
    level: int = Field(ge=1, le=6)
    text: str


class LinkInfo(BaseModel):
    text: str
    href: str
    is_external: bool


class ImageInfo(BaseModel):
    src: str
    alt: str | None = None


class FormInfo(BaseModel):
    action: str | None = None
    method: str = "get"


class ButtonInfo(BaseModel):
    text: str
    button_type: str | None = None


class InputInfo(BaseModel):
    name: str | None = None
    input_type: str = "text"
    placeholder: str | None = None
    required: bool = False


class PageMetrics(BaseModel):
    load_time_ms: int = Field(ge=0)


class BrowserIntelligenceRequest(BaseModel):
    url: HttpUrl


class BrowserIntelligenceResult(BaseModel):
    requested_url: str
    final_url: str
    title: str
    meta_description: str | None = None
    canonical_url: str | None = None
    status_code: int | None = None
    success: bool
    headings: list[HeadingInfo] = Field(default_factory=list)
    links: list[LinkInfo] = Field(default_factory=list)
    images: list[ImageInfo] = Field(default_factory=list)
    forms: list[FormInfo] = Field(default_factory=list)
    buttons: list[ButtonInfo] = Field(default_factory=list)
    inputs: list[InputInfo] = Field(default_factory=list)
    console_errors: list[str] = Field(default_factory=list)
    metrics: PageMetrics
    warnings: list[ExtractionWarning] = Field(default_factory=list)
