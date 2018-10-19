INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_BL bl)

FIND_PATH(
    BL_INCLUDE_DIRS
    NAMES bl/api.h
    HINTS $ENV{BL_DIR}/include
        ${PC_BL_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    BL_LIBRARIES
    NAMES gnuradio-bl
    HINTS $ENV{BL_DIR}/lib
        ${PC_BL_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(BL DEFAULT_MSG BL_LIBRARIES BL_INCLUDE_DIRS)
MARK_AS_ADVANCED(BL_LIBRARIES BL_INCLUDE_DIRS)

