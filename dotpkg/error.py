class DotpkgError(Exception):
    pass

class InvalidManifestError(DotpkgError):
    pass

class MissingDotpkgManifestError(DotpkgError):
    pass

class NoTargetDirError(DotpkgError):
    pass
