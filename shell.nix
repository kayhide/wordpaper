{ pkgs ? import <nixpkgs> { }
}:

let
  app = pkgs.callPackage ./. { };

in

pkgs.mkShell {
  buildInputs = with pkgs; [
    entr
    findutils
    gnumake
    shunit2
  ] ++ app.buildInputs;
}
