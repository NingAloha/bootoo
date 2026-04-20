"""Artifact domain model skeleton."""

from dataclasses import dataclass
from enum import Enum


class ArtifactKind(str, Enum):
    DISK_IMAGE = "disk-image"
    FILE_BUNDLE = "file-bundle"


@dataclass(slots=True)
class ImageArtifact:
    path: str
    kind: ArtifactKind
