{ lib
, stdenv
, buildPythonPackage
, fetchFromGitHub
, unittestCheckHook
, pythonOlder
, aiohttp
, iso8601
, typing-extensions
}:

buildPythonPackage rec {
  pname = "twitchio";
  version = "2.8.2";
  format = "setuptools";

  disabled = pythonOlder "3.7";

  src = fetchFromGitHub {
    owner = "PythonistaGuild";
    repo = "TwitchIO";
    rev = "refs/tags/v${version}";
    hash = "sha256-1o+r5S19ZCcuBx1vXb+ZGcqh+U5tOEqGrlxm2tD8EKM=";
  };

  propagatedBuildInputs = [
    aiohttp
    iso8601
    typing-extensions
  ];

  pythonImportsCheck = [
    "twitchio"
  ];
}
