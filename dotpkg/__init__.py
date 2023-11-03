import argparse
import os
import sys

from pathlib import Path

from dotpkg.commands import install_cmd, uninstall_cmd, sync_cmd, upgrade_install_manifest_cmd
from dotpkg.error import DotpkgError
from dotpkg.install import install_manifest_path
from dotpkg.options import Options
from dotpkg.utils.prompt import confirm
from dotpkg.utils.log import warn, error

if sys.version_info < (3, 10):
    print('Python version >= 3.10 is required!')
    sys.exit(1)

# CLI

COMMANDS = {
    'install': install_cmd,
    'uninstall': uninstall_cmd,
    'sync': sync_cmd,
    'upgrade-install-manifest': upgrade_install_manifest_cmd,
}

def main():
    parser = argparse.ArgumentParser(description='Dotfile package manager')
    parser.add_argument('-C', '--cwd', type=Path, default=Path.cwd(), help='The working directory for all dotpkg-related operations. Defaults to the current working directory.')
    parser.add_argument('-H', '--home', type=Path, default=Path.home(), help='The home directory for all dotpkg-related operations. Defaults to the standard home directory.')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Simulate a run without any modifications to the file system.')
    parser.add_argument('-y', '--assume-yes', action='store_true', help='Accept prompts with yes and run non-interactively (great for scripts)')
    parser.add_argument('-s', '--safe-mode', action='store_true', help='Skip any user-defined shell commands such as scripts.')
    parser.add_argument('--no-install-manifest', action='store_false', dest='update_install_manifest', help=f'Skips updating the install manifest at {install_manifest_path(Options())}.')
    parser.add_argument('command', choices=sorted(COMMANDS.keys()), help='The command to invoke')
    parser.add_argument('subargs', nargs=argparse.ZERO_OR_MORE, help='The arguments to the command.')

    args = parser.parse_args()
    opts = Options(
        cwd=args.cwd,
        home=args.home,
        dry_run=args.dry_run,
        assume_yes=args.assume_yes,
        update_install_manifest=args.update_install_manifest,
        safe_mode=args.safe_mode,
    )

    if opts.dry_run:
        warn("Performing dry run (i.e. not actually changing any files)")
    
    if os.geteuid() == 0 and (Path('/Users') in opts.home.parents or Path('/home') in opts.home.parents):
        warn(f'You appear to be running as root, but with a user home directory ({opts.home}). This is discouraged since the user cannot uninstall any root-installed packages.')
        if not confirm("Are you sure you want to do this? (Perhaps you forgot to use 'sudo -H'?)", opts):
            sys.exit(0)

    try:
        COMMANDS[args.command](args.subargs, opts)
    except DotpkgError as e:
        error(str(e))
        sys.exit(1)
