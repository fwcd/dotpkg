import argparse
import sys

from dotpkg.constants import INSTALL_MANIFEST_NAME
from dotpkg.commands import install_cmd, uninstall_cmd, sync_cmd
from dotpkg.options import Options
from dotpkg.utils.log import warn

if sys.version_info < (3, 9):
    print('Python version >= 3.9 is required!')
    sys.exit(1)

# CLI

COMMANDS = {
    'install': install_cmd,
    'uninstall': uninstall_cmd,
    'sync': sync_cmd,
}

def main():
    parser = argparse.ArgumentParser(description='Dotfile package manager')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Simulate a run without any modifications to the file system.')
    parser.add_argument('-y', '--assume-yes', action='store_true', help='Accept prompts with yes and run non-interactively (great for scripts)')
    parser.add_argument('-s', '--safe-mode', action='store_true', help='Skip any user-defined shell commands such as scripts.')
    parser.add_argument('--no-install-manifest', action='store_false', dest='update_install_manifest', help=f'Skips creating an install manifest ({INSTALL_MANIFEST_NAME}).')
    parser.add_argument('command', choices=sorted(COMMANDS.keys()), help='The command to invoke')
    parser.add_argument('subargs', nargs=argparse.ZERO_OR_MORE, help='The arguments to the command.')

    args = parser.parse_args()
    opts = Options(
        dry_run=args.dry_run,
        assume_yes=args.assume_yes,
        update_install_manifest=args.update_install_manifest,
        safe_mode=args.safe_mode,
    )

    if opts.dry_run:
        warn("Performing dry run (i.e. not actually changing any files)")

    COMMANDS[args.command](args.subargs, opts)
