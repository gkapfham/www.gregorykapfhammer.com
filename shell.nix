let
  nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/archive/04220ed6763637e5899980f98d5c8424b1079353.tar.gz";
  pkgs = import nixpkgs { config = {}; overlays = []; };
in
  pkgs.mkShell {
    packages = with pkgs; [
      (python311.withPackages (ps: with ps; [
        bibtexparser
        csscompressor
        htmlmin
        pyyaml
        rich
        rjsmin
        jupyterlab
        jupyterlab-git
        pip
        pydocstyle
        quarto
      ]))
    ];
  shellHook = ''
    echo "󰁡 Setting JUPYTER_PATH and PYTHONPATH for quarto"
    export JUPYTER_PATH=${pkgs.python311Packages.jupyterlab}/share/jupyter
    export PYTHONPATH=$PYTHONPATH:${pkgs.python311Packages.ipykernel}/${pkgs.python311.sitePackages}
    echo "󱎯 Quarto and Python Dependencies Now Available"
    echo " Suggested Commands: 'quarto preview' or 'quarto render'"
    echo " Example Script: 'python scripts/minify-files.py --verbose --force'"
  '';
  }
