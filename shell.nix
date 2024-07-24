let

  # Load all of the nix packages
  pkgs = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/04220ed6763637e5899980f98d5c8424b1079353.tar.gz") {};

  # Specify the Python packages that are available in nixpkgs
  # and should also be embedded inside of the Python used by
  # quarto. Note that if this step is not taken then running
  # the Python that is bound with quarto will not be able
  # to access additional third-party packages like rich.
  pypkgs = builtins.attrValues {
    inherit (pkgs.python311Packages) bibtexparser jupyter matplotlib pyyaml rich ;
  };

  # Make sure that the chosen version of quarto has
  # the enhanced version of Python with the packages
  system_packages = builtins.attrValues {
    inherit (pkgs) R glibcLocalesUtf8 quarto python311;
  };

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

# let
#   nixpkgs = import <nixpkgs> {};
#   myPython = nixpkgs.python3.withPackages (ps: with ps; [
#     jupyter
#     ipython
#     rich
#     # Add your Python packages here
#   ]);
# in
#   nixpkgs.mkShell {
#     buildInputs = [
#       (nixpkgs.quarto.override { python3 = myPython; })
#       # Add other packages here
#     ];
#   }

# let
#   nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/archive/04220ed6763637e5899980f98d5c8424b1079353.tar.gz";
#   pkgs = import nixpkgs { config = {}; overlays = []; };
#   myPython = pkgs.python311.withPackages (ps: with ps; [
#     bibtexparser
#     csscompressor
#     htmlmin
#     pyyaml
#     rich
#     rjsmin
#     ipykernel
#     jupyterlab
#     jupyterlab-git
#     pip
#     pydocstyle
#   ]);
# in
#   pkgs.mkShell {
#     packages = with pkgs; [
#       myPython
#       (pkgs.quarto.override { python3 = myPython; })
#     ];
#   shellHook = ''
#     # echo "󰁡 Setting JUPYTER_PATH and PYTHONPATH for quarto"
#     # export JUPYTER_PATH=${pkgs.python311Packages.jupyterlab}/share/jupyter
#     # export PYTHONPATH=$PYTHONPATH:${pkgs.python311Packages.ipykernel}/${pkgs.python311.sitePackages}
#     echo " Suggested Commands: 'quarto preview' or 'quarto render'"
#     echo "󰢌 Poetry Reminder: Use 'poetry shell' before running Python scripts"
#     echo " Example Script: 'python scripts/minify-files.py --verbose --force'"
#   '';
#   }

# let
#   nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/archive/04220ed6763637e5899980f98d5c8424b1079353.tar.gz";
#   pkgs = import nixpkgs { config = {}; overlays = []; };
# in
#   pkgs.mkShell {
#     packages = with pkgs; [
#       myPython = (python311.withPackages (ps: with ps; [
#         bibtexparser
#         csscompressor
#         htmlmin
#         pyyaml
#         rich
#         rjsmin
#         ipykernel
#         jupyterlab
#         jupyterlab-git
#         pip
#         pydocstyle
#         quarto
#       ]))
#       quarto.override { python3 = myPython; }
#     ];
#   shellHook = ''
#     # echo "󰁡 Setting JUPYTER_PATH and PYTHONPATH for quarto"
#     # export JUPYTER_PATH=${pkgs.python311Packages.jupyterlab}/share/jupyter
#     # export PYTHONPATH=$PYTHONPATH:${pkgs.python311Packages.ipykernel}/${pkgs.python311.sitePackages}
#     echo " Suggested Commands: 'quarto preview' or 'quarto render'"
#     echo "󰢌 Poetry Reminder: Use 'poetry shell' before running Python scripts"
#     echo " Example Script: 'python scripts/minify-files.py --verbose --force'"
#   '';
#   }
