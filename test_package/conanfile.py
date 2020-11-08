from conans import ConanFile, CMake
import platform

class LibfreenectTestConan(ConanFile):
    generators = 'cmake'
    requires = (
        'llvm/5.0.2-1@vuo/stable',
        'macos-sdk/11.0-0@vuo/stable',
    )

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy('*', src='bin', dst='bin')
        self.copy('*', src='lib', dst='lib')

    def test(self):
        self.run('./bin/test_package')

        # Ensure we only link to system libraries and to libraries we built.
        if platform.system() == 'Darwin':
            self.run('! (otool -L lib/libfreenect.dylib | tail +3 | egrep -v "^\s*(/usr/lib/|/System/|@rpath/)")')
            self.run('! (otool -L lib/libfreenect.dylib | fgrep "libstdc++")')
            self.run('! (otool -l lib/libfreenect.dylib | grep -A2 LC_RPATH | cut -d"(" -f1 | grep "\s*path" | egrep -v "^\s*path @(executable|loader)_path")')
        elif platform.system() == 'Linux':
            self.run('! (ldd lib/libfreenect.so | grep -v "^lib/" | grep "/" | egrep -v "(\s(/lib64/|(/usr)?/lib/x86_64-linux-gnu/)|test_package/build)")')
            self.run('! (ldd lib/libfreenect.so | fgrep "libstdc++")')
        else:
            raise Exception('Unknown platform "%s"' % platform.system())
