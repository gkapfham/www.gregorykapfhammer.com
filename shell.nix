# Note: Enter this shell before running the following commands

# Command to enter the shell environment: nix-shell shell.nix
# Command to run Quarto to make web site: quarto render
# Command to run Quarto to perform a preview: quarto preview

# Note: This shell environment does not contain the minify-html
# Python package because it is not included in the nixpkgs
# repository. However, this is available through the Poetry shell
# when you type the command: poetry shell in the directory that
# contains the pyproject.toml file. Importantly, note that the
# quarto commands do not "pick up" the poetry shell's environment.

let

  # Load all of the nix packages
  pkgs = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/04220ed6763637e5899980f98d5c8424b1079353.tar.gz") {};

  # Specify the Python packages that are available in nixpkgs
  # and should also be embedded inside of the Python used by
  # quarto. Note that if this step is not taken then running
  # the Python that is bound with quarto will not be able
  # to access additional third-party packages like rich.
  pypkgs = builtins.attrValues {
    inherit (pkgs.python312Packages) bibtexparser jupyter matplotlib pyyaml rich ;
  };

  # Make sure that the chosen version of quarto has
  # the enhanced version of Python with the packages
  system_packages = builtins.attrValues {
    inherit (pkgs) R glibcLocalesUtf8 quarto python312;
  };

  # Create a shell environment that includes the
  # Python packages and the standard system packages
  in
  pkgs.mkShell {
    LOCALE_ARCHIVE = if pkgs.system == "x86_64-linux" then  "${pkgs.glibcLocalesUtf8}/lib/locale/locale-archive" else "";
    LANG = "en_US.UTF-8";
    LC_ALL = "en_US.UTF-8";
    LC_TIME = "en_US.UTF-8";
    LC_MONETARY = "en_US.UTF-8";
    LC_PAPER = "en_US.UTF-8";
    LC_MEASUREMENT = "en_US.UTF-8";
    buildInputs = [ pypkgs system_packages  ];
  }
