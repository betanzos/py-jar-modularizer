# JarModularizer
This is the pythoner brother of [JarModularizer](https://github.com/betanzos/jar-modularizer) project. It's a lightweight command line python tool for make non-modular JAR files compatible with Java Platform Module System. It's a translate of [JarModularizer](https://github.com/betanzos/jar-modularizer) code with many changes since python is very different from java.

## Usage
The way PyJarModularizer work is simple and almost identical to how [JarModularizer](https://github.com/betanzos/jar-modularizer) does it. It need a configuration JSON file, called [modularization descriptor](#modularization-descriptor-format), with the description of how each JAR file, called artifact, will should become in a java module, source directory path which is where non-modular JARs files will be found; and JDK home directory.

### Prerequisites
* [JDK 9 or later](https://www.oracle.com/technetwork/java/javase/overview/index.html) because is requires for compile the module descriptors.
* [Python 3.7](https://www.python.org/).

### Example
From python:
```
python jarmod.py DESCRIPTOR SOURCE --jdk-home /path/to/jdk
```
Using an native executable (go to [dist](dist)):
```
jarmod DESCRIPTOR SOURCE --jdk-home /path/to/jdk
```
Command above will deposit the new modular JAR copies in `SOURCE/mods` directory with fallowing name pattern: original.jar-mod.jar (ej. for log4j-1.2.17.jar new file name will be log4j-1.2.17.jar-mod.jar).

***Note:*** If ```--jdk-home``` param is missing, path to JDK home directory will be taken from JAVA_HOME environment variable.

#### Important!
Only that files which name (including .jar extension) match with an entry in [modularization descriptor](#modularization-descriptor-format) will be processed.

## Making executable files (optional)
If you want to build an executable native file (like found in [dist](dist)) for any platform (Windows, Linux and Mac OS X), [PyInstaller](https://www.pyinstaller.org/) could be used (or any other tool compatible with Python 3.7).

### Installing PyInstaller
Most easy way is from PyPI:
```
pip install pyinstaller
```

### Build executable
For bundle all the project in a single file, we must to use following command: (see [exe-build-commands.txt](exe-build-commands.txt))

_Windows_
```
pyinstaller --onefile --name jarmod-1.0.0-win<arch> --icon icon\jigsaw-64.ico jarmod.py
```
_Linux and Mac OS X (Mac OS X theoretically)_
```
pyinstaller --onefile --name jarmod-1.0.0-<osname><arch> jarmod.py
```
Go to PyInstaller [offical documentation](https://pyinstaller.readthedocs.io/en/stable/) for more details and options.

## Getting help
If `--help` param is using, tool's help will be displayed in the terminal.

## Modularization descriptor format
As was mentioned above, the modularization descriptor is a JSON file. Below show it format.

***Note:*** JSON format doesn't allow comments, so java-style inline comment texts are only for descriptive purposes.
```
[
    {
        "name": "log4j-1.2.17.jar",// artifact name
        "module": {// module entry
            "name": "log4j",// future module name
            "exportsPackages": [// (optional) list of artifact's packages to be exported by the future module. Default is all artifact non-empty packages
                "org.apache.log4j",
                "org.apache.log4j.net"
            ],
            "requiresModules": [// (optional) list of requires directive to be included in module-info.java. Dafault is none diretive
                "java.base",
                "java.desktop",
                "java.management",
                "java.naming",
                "java.sql",
                "java.xml"
            ]
        }
    },
    ...
]
```

## Author
Eduardo Betanzos [@ebetanzosm](https://twitter.com/ebetanzosm)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.