from dotpkg.constants import IGNORED_NAMES
from dotpkg.model import DotpkgRef, DotpkgRefs
from dotpkg.options import Options

# Dotpkg resolution

def cwd_dotpkgs(opts: Options) -> DotpkgRefs:
    cwd = opts.cwd.resolve()

    # Prefer current directory if it contains a manifest
    cwd_ref = DotpkgRef(cwd)
    if cwd_ref.manifest_path.exists():
        return DotpkgRefs(
            refs=[cwd_ref],
            is_batch=False,
        )
    
    # Otherwise resolve child directories
    return DotpkgRefs(
        refs=[
            ref
            for p in cwd.iterdir()
            for ref in [DotpkgRef(p)]
            if not p.name in IGNORED_NAMES and ref.manifest_path.exists()
        ],
        is_batch=True,
    )
