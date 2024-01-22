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
      git
      pipx
      poetry
      prettierd
      python3
      quarto
      zsh
    ];
  shellHook = ''
    echo "✨ Running Quarto Preview with the 'develop' profile"
    quarto preview --profile develop
  '';
  }
