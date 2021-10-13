{ pkgs ? import <nixpkgs> { }
}:

let
  inherit (pkgs) lib stdenv;

in

stdenv.mkDerivation rec {
  pname = "wordpaper";
  version = "0.1.0";

  src = ./src;

  nativeBuildInputs = with pkgs; [
    makeWrapper
  ];

  buildInputs = with pkgs; [
    coreutils
    curl
    findutils
    gnugrep
    gnused
    imagemagick
    jq
    ncurses
  ];

  installPhase = ''
    mkdir -p $out
    cp -r . $out/bin
    wrapProgram $out/bin/wordpaper \
      --argv0 wordpaper \
      --set VERSION '${version}' \
      --prefix PATH : ${lib.makeBinPath buildInputs}
  '';

  meta = with lib; {
    description = "Command line tool to generate images which help you remembering words";
    license = licenses.mit;
    maintainers = with maintainers; [ kayhide ];
  };
}
