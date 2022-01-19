# Dotpkg

A package manager for your dotfiles.

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

Optionally, you can specify keys such as `requiresOnPath` too, which will only install the package if a given binary is found on your `PATH` (useful if your config targets some application). Additionally, `targetDir` configures the search path to symlink the files into some other directory than your home (`dotpkg` will use the first directory that exists, this is useful to cross-platform packages).

For example, a package that manages configurations for Visual Studio Code could look like this:

```json
{
  "name": "vscode",
  "description": "Visual Studio Code settings and keybindings",
  "requiresOnPath": ["code"],
  "targetDir": [
    "${home}/.config/Code",
    "${home}/Library/Application Support/Code"
  ]
}
```
