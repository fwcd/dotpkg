# Dotpkg

[![PyPI](https://img.shields.io/pypi/v/dotpkg)](https://pypi.org/project/dotpkg)
[![Typecheck](https://github.com/fwcd/dotpkg/actions/workflows/typecheck.yml/badge.svg)](https://github.com/fwcd/dotpkg/actions/workflows/typecheck.yml)

A package manager for your dotfiles.

## Why Dotpkg?

- **Lightweight**: Pure Python 3.9 with no dependencies
- **JSON-configurable**: Easy to write, includes a schema for code completion
- **Cross-platform**: Runs on Linux, macOS and Windows
- **Flexible**: Configurable target locations, ignore lists, rename rules and more

## Usage

First make sure to have Python 3.9+ installed. To create a dotfile package, set up a folder with the following layout (the top-level folder is assumed to be some folder, e.g. a Git repo, where you store all of your dotfiles):

```
dotfiles
└─my-package
  ├─dotpkg.json
  ├─.some-dotfile-one
  ├─.some-dotfile-two
    ...
```

A minimal `dotpkg.json` is structured as follows:

```json
{
  "name": "my-package",
  "description": "Description of my package"
}
```

Navigating into `dotfiles` and running `dotpkg install my-package` will then symlink `.some-dotfile-one` and `.some-dotfile-two` into your home directory.

> Note that when running on Windows, unprivileged users might not be able to create symlinks, a feature that `dotpkg` relies on. Enabling `Developer Mode` in your Windows Settings (from an administrator account) will permit this. Also, you may need to substitute `python3 [path/to/dotpkg]` for `dotpkg` since Windows does not support Unix-style shebangs.

Optionally, you can specify keys such as `requiresOnPath` too, which will only install the package if a given binary is found on your `PATH` (useful if your config targets some application). Additionally, `targetDir` configures the search path to symlink the files into some other directory than your home (`dotpkg` will use the first directory that exists, this is useful to cross-platform packages).

For example, a package that manages configurations for Visual Studio Code could look like this:

```json
{
  "name": "vscode",
  "description": "Visual Studio Code settings and keybindings",
  "requiresOnPath": ["code"],
  "targetDir": [
    "${home}/.config/Code",
    "${home}/Library/Application Support/Code",
    "${home}/AppData/Roaming/Code"
  ]
}
```

A full JSON schema for the `dotpkg.json` manifests can be found [here](dotpkg.schema.json).

> Note that you can add the schema to your VSCode settings to get autocompletion in `dotpkg.json` files by specifying `json.schemas`:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["dotpkg.json"],
      "url": "https://raw.githubusercontent.com/fwcd/dotpkg/main/dotpkg.schema.json"
    }
  ]
}
```

Alternatively, you can specify the schema individually in each `dotpkg.json`:

```json
{
  "$schema": "https://raw.githubusercontent.com/fwcd/dotpkg/main/dotpkg.schema.json"
}
```
