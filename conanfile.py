from conans import ConanFile, CMake, tools
import os
import platform
import shutil

class LibfreenectConan(ConanFile):
    name = 'libfreenect'

    source_version = '0.6.1'
    package_version = '0'
    version = '%s-%s' % (source_version, package_version)

    build_requires = (
        'llvm/5.0.2-1@vuo/stable',
        'macos-sdk/11.0-0@vuo/stable',
    )
    requires = 'libusb/1.0.23-0@vuo/stable'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://github.com/OpenKinect/libfreenect'
    license = 'https://github.com/OpenKinect/libfreenect/blob/master/APACHE20'
    description = 'Driver for the Kinect for Windows v1 / Kinect for Xbox 360'
    source_dir = 'libfreenect-%s' % source_version
    generators = 'cmake'

    build_dir = '_build'
    install_dir = '_install'

    def requirements(self):
        if platform.system() == 'Linux':
            self.requires('patchelf/0.10pre-1@vuo/stable')
        elif platform.system() != 'Darwin':
            raise Exception('Unknown platform "%s"' % platform.system())

    def source(self):
        tools.get('https://github.com/OpenKinect/libfreenect/archive/v%s.tar.gz' % self.source_version,
                  sha256='a2e426cf42d9289b054115876ec39502a1144bc782608900363a0c38056b6345')

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
        cmake.definitions['CONAN_DISABLE_CHECK_COMPILER'] = True
        cmake.definitions['CMAKE_BUILD_TYPE'] = 'Release'
        cmake.definitions['CMAKE_C_COMPILER'] = self.deps_cpp_info['llvm'].rootpath + '/bin/clang'
        cmake.definitions['CMAKE_C_FLAGS'] = cmake.definitions['CMAKE_CXX_FLAGS'] = '-Oz'
        cmake.definitions['CMAKE_INSTALL_PREFIX'] = '%s/%s' % (os.getcwd(), self.install_dir)
        if platform.system() == 'Darwin':
            cmake.definitions['CMAKE_OSX_ARCHITECTURES'] = 'x86_64;arm64'
            cmake.definitions['CMAKE_OSX_DEPLOYMENT_TARGET'] = '10.11'
            cmake.definitions['CMAKE_OSX_SYSROOT'] = self.deps_cpp_info['macos-sdk'].rootpath
        cmake.definitions['CMAKE_CXX_COMPILER'] = self.deps_cpp_info['llvm'].rootpath + '/bin/clang++'

        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            cmake.configure(source_dir='../%s' % self.source_dir,
                            build_dir='.')
            cmake.build()
            cmake.install()

        with tools.chdir(self.install_dir):
            if platform.system() == 'Darwin':
                shutil.move('lib/libfreenect.%s.dylib' % self.source_version, 'lib/libfreenect.dylib')
                self.run('install_name_tool -id @rpath/libfreenect.dylib lib/libfreenect.dylib')
            elif platform.system() == 'Linux':
                shutil.move('lib/libfreenect.so.%s' % self.source_version, 'lib/libfreenect.so')
                patchelf = self.deps_cpp_info['patchelf'].rootpath + '/bin/patchelf'
                self.run('%s --set-soname libfreenect.so lib/libfreenect.so' % patchelf)

    def package(self):
        if platform.system() == 'Darwin':
            libext = 'dylib'
        elif platform.system() == 'Linux':
            libext = 'so'
        else:
            raise Exception('Unknown platform "%s"' % platform.system())

        self.copy('*.h', src='%s/include' % self.install_dir, dst='include')
        self.copy('libfreenect.%s' % libext, src='%s/lib' % self.install_dir, dst='lib')

        self.copy('%s.txt' % self.name, src=self.source_dir, dst='license')

    def package_info(self):
        self.cpp_info.libs = ['freenect']
