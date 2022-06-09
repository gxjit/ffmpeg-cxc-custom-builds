from argparse import ArgumentParser
from datetime import datetime
from functools import partial
from os import environ
from pathlib import Path
from shutil import copytree
from subprocess import run
from sys import exit
from tempfile import TemporaryDirectory
from zipfile import ZipFile


def parseArgs():
    parser = ArgumentParser()
    buildSelect = parser.add_mutually_exclusive_group(required=True)
    buildSelect.add_argument("-l", "--linux64", action="store_true")
    buildSelect.add_argument("-w", "--mingw64", action="store_true")
    # parser.add_argument("-uh", "--home", action="store_true")

    return parser.parse_args()


pargs = parseArgs()

# repoName = "ffmpeg-cxc-custom-build"
# repoUrl = f"https://github.com/gxjit/{repoName}.git"
subModule = "ffmpeg-cxc-build"

fDate = lambda: datetime.now().strftime("%d-%m-%y")

if pargs.linux64:
    buildType = "native"
    buildTarget = "linux64"
elif pargs.mingw64:
    buildType = "cxc"
    buildTarget = "mingw64"
else:
    exit()

buildName = f"ffmpeg-{buildTarget}-build"

td = TemporaryDirectory(ignore_cleanup_errors=True)
buildRoot = Path.cwd()  # if not pargs.home else Path.home()
rootPath = Path(td.name)  # buildRoot / buildName
hintsFile = rootPath / f"ffmpeg-{buildType}-build-hints-custom"
buildLog = rootPath / f"{buildName}.log"
distDir = (
    Path(environ.get("dist_dir"))  # type: ignore
    if environ.get("dist_dir")
    else rootPath / "dist"
)
assetsZip = distDir / f"{buildName}-{fDate()}.zip"

cmdPath = f"{rootPath}/{subModule}/ffmpeg-{buildType}-{buildTarget}"

if not pargs.mingw64:
    cmdPath = cmdPath.replace(f"-{buildTarget}", "")

print(f"\nBuilding for {buildTarget} in {rootPath}\n")

deps = (
    "autoconf automake autopoint build-essential libarchive-tools cmake "
    "git-core gperf libtool mercurial meson nasm pkg-config "
    "python3-lxml ragel subversion texinfo yasm wget"
)

if pargs.mingw64:
    deps = f"{deps} g++-mingw-w64 gcc-mingw-w64"

runP = partial(run, shell=True, check=True)

runP(f"sudo apt-get -y install {deps}")

if not rootPath.exists():
    rootPath.mkdir()

copytree(Path.cwd(), rootPath, dirs_exist_ok=True)

usrEnv = environ.copy()
usrEnv["ROOT_PATH"] = str(rootPath)
usrEnv["HINTS_FILE"] = str(hintsFile)

runP(f"chmod +rx {cmdPath}")

runP = partial(runP, capture_output=True, text=True)

cmdOut = runP(f"bash {cmdPath}", env=usrEnv)
# bash {cmdPath} 2>&1 | tee {buildLog}

built = list(rootPath.rglob("bin/ff*"))

if len(built) == 3:
    buildLog.write_text(cmdOut.stdout)
    print(cmdOut.stdout)
else:
    buildLog.write_text(cmdOut.stderr)
    print(cmdOut.stderr)
    exit(1)


if not distDir.exists():
    distDir.mkdir()

with ZipFile(assetsZip, "w") as zipit:
    for f in built:
        zipit.write(f, f.name)
    zipit.write(buildLog, buildLog.name)

td.cleanup()

# runP("pip3 install -U --user meson")
# import stat
# chmod(cmdPath, stat.S_IRUSR)
# chmod(cmdPath, stat.S_IXUSR)
