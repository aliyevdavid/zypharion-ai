from pydantic import BaseModel, Field, HttpUrl


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