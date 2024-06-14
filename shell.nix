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
    echo "󱎯 Quarto and Python Dependencies Now Available"
    echo " Suggested Commands: 'quarto preview' or 'quarto render'"
  '';
  }
