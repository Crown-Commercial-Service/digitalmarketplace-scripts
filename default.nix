{
  pkgs ? import <nixpkgs> {},
  pythonPackages ? pkgs.python36Packages,
  forTest ? true
}:
{
  digitalMarketplaceScriptsEnv = pkgs.stdenv.mkDerivation {
    name = "digitalmarketplace-scripts-env";
    buildInputs = [
      pythonPackages.virtualenv
      pkgs.libffi
      pkgs.libyaml
      # for `cryptography`
      pkgs.openssl
    ] ++ pkgs.stdenv.lib.optionals (!pkgs.stdenv.isDarwin) [
      # package not available on darwin for now - sorry you're on your own...
      pkgs.wkhtmltopdf
    ] ++ pkgs.stdenv.lib.optionals forTest [
      # for lxml
      pkgs.libxml2
      pkgs.libxslt
    ];

    hardeningDisable = pkgs.stdenv.lib.optionals pkgs.stdenv.isDarwin [ "format" ];

    VIRTUALENV_ROOT = "venv${pythonPackages.python.pythonVersion}";
    VIRTUAL_ENV_DISABLE_PROMPT = "1";
    SOURCE_DATE_EPOCH = "315532800";

    # if we don't have this, we get unicode troubles in a --pure nix-shell
    LANG="en_GB.UTF-8";

    shellHook = ''
      if [ ! -e $VIRTUALENV_ROOT ]; then
        ${pythonPackages.virtualenv}/bin/virtualenv $VIRTUALENV_ROOT
      fi
      source $VIRTUALENV_ROOT/bin/activate
      pip install -r requirements${pkgs.stdenv.lib.optionalString forTest "_for_test"}.txt
    '';
  };
}
