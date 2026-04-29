"""User-facing domain errors for lettersign."""


class LettersignError(Exception):
    """Base exception for expected failures (config, paths, SVG, etc.)."""


class InvalidProjectNameError(LettersignError):
    """Raised when a project name is not a safe single path component."""


class InvalidConfigError(LettersignError):
    """Raised when a project TOML value does not satisfy the lettersign schema."""


class MissingInputSvgError(LettersignError):
    """Raised when a project build is requested but the input SVG is missing."""
