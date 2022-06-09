parser.add_argument("-t", "--tests", action="store_false")

testLog = rootPath / f"{buildName}-test.log"

if pargs.tests:
    deps = f"{deps} wine"

if pargs.tests:  # Tests
    testOut = []

    for f in built:
        try:
            testOut.append(runP(["file", str(f)]))

            if pargs.mingw64:
                # runP("sudo apt-get -y install wine")  # move this up
                testOut.append(runP(f'wine "{str(f)}" -map -version'))
            else:
                testOut.append(runP(["ldd", str(f)]))
                testOut.append(runP([str(f), "-version"]))

        except CalledProcessError as e:
            print(e)
            print(e.cmd)
            print(e.stderr)
            print(e.stdout)

    # checkErrs = "".join(o.stderr for o in testOut).strip()
    checkErrs = sum([o.returncode for o in testOut])

    if checkErrs:
        print("Tests Failed -> \n" + "\n\n".join(o.stderr for o in testOut))
        exit(1)

    testOut = "\n\n".join(o.stdout for o in testOut)

    testLog.write_text(testOut)
    print(testOut)

# readelf

if pargs.tests:
    zipit.write(testLog, testLog.name)
