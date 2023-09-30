# NOTE: This file is auto-generated from schemas/installs.schema.json via scripts/generate-models
# Please do not edit it manually and adjust/re-run the script instead!

from .installs_v1 import InstallsV1Manifest
from .installs_v2 import InstallsV2Manifest
from typing import Union

InstallsManifest = Union[InstallsV1Manifest, InstallsV2Manifest]

