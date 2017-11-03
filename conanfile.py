from conans import ConanFile, CMake, tools
import shutil

class LibfreenectConan(ConanFile):
    name = 'libfreenect'
    version = '0.5.6'
    requires = 'libusb/1.0.21@vuo/stable'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://github.com/vuo/conan-libfreenect'
    license = 'https://github.com/OpenKinect/libfreenect/blob/master/APACHE20'
    description = 'Driver for the Kinect for Windows v1 / Kinect for Xbox 360'
    source_dir = 'libfreenect-%s' % version
    build_dir = '_build'
    generators = 'cmake'

    def source(self):
        tools.get('https://github.com/OpenKinect/libfreenect/archive/v%s.tar.gz' % self.version,
                  sha256='5ec1973cd01fd864f4c5ccc84536aa2636d0be768ba8b1c2d99026f3cd1abfd3')

        tools.replace_in_file('%s/CMakeLists.txt' % self.source_dir,
                              'PROJECT(libfreenect)',
                              '''
                              PROJECT(libfreenect)
                              include(../conanbuildinfo.cmake)
                              conan_basic_setup()
                              ''')

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
            cmake.definitions['CMAKE_C_COMPILER'] = '/usr/local/bin/clang'
            cmake.definitions['CMAKE_C_FLAGS'] = cmake.definitions['CMAKE_CXX_FLAGS'] = '-Oz -mmacosx-version-min=10.8'
            cmake.definitions['CMAKE_CXX_COMPILER'] = '/usr/local/bin/clang++'
            cmake.configure(source_dir='../%s' % self.source_dir,
                            build_dir='.')
            cmake.build()

            # They forgot to update the version number.
            shutil.move('lib/libfreenect.0.5.5.dylib', 'lib/libfreenect.dylib')

            self.run('install_name_tool -id @rpath/libfreenect.dylib lib/libfreenect.dylib')

    def package(self):
        self.copy('*.h', src='%s/include' % self.source_dir, dst='include/libfreenect')
        self.copy('libfreenect.dylib', src='%s/lib' % self.build_dir, dst='lib')

    def package_info(self):
        self.cpp_info.libs = ['freenect']
