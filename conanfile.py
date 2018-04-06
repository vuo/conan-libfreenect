from conans import ConanFile, CMake, tools
import platform
import shutil

class LibfreenectConan(ConanFile):
    name = 'libfreenect'

    source_version = '0.5.6'
    package_version = '3'
    version = '%s-%s' % (source_version, package_version)

    build_requires = 'llvm/3.3-5@vuo/stable'
    requires = 'libusb/1.0.21-3@vuo/stable'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://github.com/vuo/conan-libfreenect'
    license = 'https://github.com/OpenKinect/libfreenect/blob/master/APACHE20'
    description = 'Driver for the Kinect for Windows v1 / Kinect for Xbox 360'
    source_dir = 'libfreenect-%s' % source_version
    build_dir = '_build'
    generators = 'cmake'

    def requirements(self):
        if platform.system() == 'Linux':
            self.requires('patchelf/0.10pre-1@vuo/stable')
        elif platform.system() != 'Darwin':
            raise Exception('Unknown platform "%s"' % platform.system())

    def source(self):
        tools.get('https://github.com/OpenKinect/libfreenect/archive/v%s.tar.gz' % self.source_version,
                  sha256='5ec1973cd01fd864f4c5ccc84536aa2636d0be768ba8b1c2d99026f3cd1abfd3')

        tools.replace_in_file('%s/CMakeLists.txt' % self.source_dir,
                              'PROJECT(libfreenect)',
                              '''
                              PROJECT(libfreenect)
                              include(../conanbuildinfo.cmake)
                              conan_basic_setup()
                              ''')

        self.run('mv %s/APACHE20 %s/%s.txt' % (self.source_dir, self.source_dir, self.name))

        # Ensure libfreenect uses the version of libusb that we built.
        tools.replace_in_file('%s/CMakeLists.txt' % self.source_dir,
                              'find_package(libusb-1.0 REQUIRED)',
                              '''
                              SET(LIBUSB_1_INCLUDE_DIRS ${CONAN_INCLUDE_DIRS_LIBUSB}/libusb-1.0)
                              SET(CMAKE_SHARED_LINKER_FLAGS -l${CONAN_LIBS_LIBUSB})
                              ''')

    def build(self):
        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            cmake = CMake(self)
            cmake.definitions['BUILD_AS3_SERVER'] = False
            cmake.definitions['BUILD_CPP'] = False
            cmake.definitions['BUILD_CV'] = False
            cmake.definitions['BUILD_C_SYNC'] = False
            cmake.definitions['BUILD_EXAMPLES'] = False
            cmake.definitions['BUILD_FAKENECT'] = False
            cmake.definitions['BUILD_OPENNI2_DRIVER'] = False
            cmake.definitions['BUILD_PYTHON'] = False
            cmake.definitions['BUILD_PYTHON2'] = False
            cmake.definitions['BUILD_PYTHON3'] = False
            cmake.definitions['BUILD_REDIST_PACKAGE'] = True
            cmake.definitions['CMAKE_C_COMPILER'] = self.deps_cpp_info['llvm'].rootpath + '/bin/clang'
            cmake.definitions['CMAKE_C_FLAGS'] = cmake.definitions['CMAKE_CXX_FLAGS'] = '-Oz -mmacosx-version-min=10.10'
            cmake.definitions['CMAKE_CXX_COMPILER'] = self.deps_cpp_info['llvm'].rootpath + '/bin/clang++'
            cmake.configure(source_dir='../%s' % self.source_dir,
                            build_dir='.')
            cmake.build()

            # They forgot to update the version number.
            if platform.system() == 'Darwin':
                shutil.move('lib/libfreenect.0.5.5.dylib', 'lib/libfreenect.dylib')
                self.run('install_name_tool -id @rpath/libfreenect.dylib lib/libfreenect.dylib')
            elif platform.system() == 'Linux':
                self.run('ls -lR')
                shutil.move('lib/libfreenect.so.0.5.5', 'lib/libfreenect.so')
                patchelf = self.deps_cpp_info['patchelf'].rootpath + '/bin/patchelf'
                self.run('%s --set-soname libfreenect.so code/libfreenect.so' % patchelf)

    def package(self):
        if platform.system() == 'Darwin':
            libext = 'dylib'
        elif platform.system() == 'Linux':
            libext = 'so'
        else:
            raise Exception('Unknown platform "%s"' % platform.system())

        self.copy('*.h', src='%s/include' % self.source_dir, dst='include/libfreenect')
        self.copy('libfreenect.%s' % libext, src='%s/lib' % self.build_dir, dst='lib')

        self.copy('%s.txt' % self.name, src=self.source_dir, dst='license')

    def package_info(self):
        self.cpp_info.libs = ['freenect']
