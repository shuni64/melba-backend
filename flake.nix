{
  description = "melba-backend";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system: 
      let
        pkgs = import nixpkgs { inherit system; };
        websocketsNew = pkgs.python311Packages.callPackage ./websockets.nix {};
        twitchio = pkgs.python311Packages.callPackage ./twitchio.nix {};
      in {
        devShell = pkgs.mkShell rec {
          stdenv = pkgs.clangStdenv;
          nativeBuildInputs = with pkgs; [
            ffmpeg
            (python311.withPackages(ps: with ps; [ websocketsNew requests mutagen pydub twitchio aiohttp ]))
          ];
        };
    }
  );
}

