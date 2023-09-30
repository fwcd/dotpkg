from .installs_v1 import InstallsV1Manifest
from .installs_v2 import InstallsV2Manifest
from typing import Union

InstallsManifest = Union[InstallsV1Manifest, InstallsV2Manifest]

