# PyInstaller (http://www.pyinstaller.org) use module:
# Module to create an executable out of python scripts
# Makespec.py is the python script which creates the spec file out of the python sript.
# Build.py will create an executable (same location as spec file) out of the spec file. This step
# will copy all needed loadable modules
# Makespec.py options are available through the SET_SOURCE_FILES_PROPERTIES, eg:
#
# SET_SOURCE_FILES_PROPERTIES(hello.py PROPERTIES UPX ON)
# ADD_PI_EXECUTABLE(hello hello.py)
# 
# An important option is PYTHONPATH it needs to be specified so that modules can be found properly
# This is a set of directory separated by ':', eg:
# SET_SOURCE_FILES_PROPERTIES(hello.py PROPERTIES PYTHONPATH "/tmp:/opt")


MACRO(ADD_PI_EXECUTABLE PI_TARGET_NAME PYTHON_FILENAME)
  # python installer creates a directory names exe.py -> exe
  GET_FILENAME_COMPONENT(PI_NAME ${PYTHON_FILENAME} NAME_WE)
  #SET(PI_NAME ${PI_TARGET_NAME})

#Step 1: Makespec.py
  # First need to find the options for Makespec.py user requested:
  SET(MAKESPEC_OPTIONS)
  GET_SOURCE_FILE_PROPERTY(makespec_debug ${PYTHON_FILENAME} DEBUG)
  IF(makespec_debug)
    SET(MAKESPEC_OPTIONS "${MAKESPEC_OPTIONS} -d")
  ENDIF(makespec_debug)
  GET_SOURCE_FILE_PROPERTY(makespec_filedep ${PYTHON_FILENAME} FILE_DEPLOYMENT)
  IF(makespec_filedep)
    SET(MAKESPEC_OPTIONS "${MAKESPEC_OPTIONS} -F")
  ENDIF(makespec_filedep)
  GET_SOURCE_FILE_PROPERTY(makespec_pythonpath ${PYTHON_FILENAME} PYTHONPATH)
  IF(makespec_pythonpath)
    SET(MAKESPEC_OPTIONS "${MAKESPEC_OPTIONS} -p ${makespec_pythonpath}")
  ENDIF(makespec_pythonpath)
  GET_SOURCE_FILE_PROPERTY(makespec_upx ${PYTHON_FILENAME} UPX)
  IF(makespec_upx)
    SET(MAKESPEC_OPTIONS "${MAKESPEC_OPTIONS} -X")
  ENDIF(makespec_upx)
  GET_SOURCE_FILE_PROPERTY(makespec_strip ${PYTHON_FILENAME} STRIP)
  IF(makespec_strip)
    SET(MAKESPEC_OPTIONS "${MAKESPEC_OPTIONS} -s")
  ENDIF(makespec_strip)
  # By default Build.py is console : -c 
  GET_SOURCE_FILE_PROPERTY(makespec_windowed ${PYTHON_FILENAME} WINDOWED)
  IF(makespec_windowed)
    SET(MAKESPEC_OPTIONS "${MAKESPEC_OPTIONS} -w")
  ENDIF(makespec_windowed)

# to split space correctly:
# Decide where to output the spec file, since it will decide where the exe (Build.py) will be:
  SET(MAKESPEC_OUTPUT_PATH ${CMAKE_CURRENT_BINARY_DIR})
  SET(MAKESPEC_OPTIONS "${MAKESPEC_OPTIONS} -o ${MAKESPEC_OUTPUT_PATH}")
  SET(MAKESPEC_FILENAME ${MAKESPEC_OUTPUT_PATH}/${PI_NAME}.spec)

  GET_SOURCE_FILE_PROPERTY(python_filename_location ${PYTHON_FILENAME} LOCATION)
# Always finish with that:
  SEPARATE_ARGUMENTS(MAKESPEC_OPTIONS)
  ADD_CUSTOM_COMMAND(
    OUTPUT    ${MAKESPEC_FILENAME}
    COMMAND   python ${PI_MAKESPEC}
    ARGS      ${MAKESPEC_OPTIONS} ${python_filename_location}
    DEPENDS   ${python_filename_location}
    COMMENT   "Generating .spec for ${PI_NAME}"
  )

# Step 2: Build.py
# $ python Build.py ${PyInstaller_PATH}/hello/hello.spec
# -> ${PyInstaller_PATH}/${PI_NAME}/dist${PI_NAME}/${PI_NAME}.${EXTENSION}
  SET(BUILD_OPTIONS)
  GET_SOURCE_FILE_PROPERTY(build_optimized ${PYTHON_FILENAME} OPTIMIZED)
  IF(build_optimized)
    SET(BUILD_OPTIONS "${BUILD_OPTIONS} -O")
  ENDIF(build_optimized)

  SEPARATE_ARGUMENTS(BUILD_OPTIONS)
  ADD_CUSTOM_COMMAND(
# FIXME: Need executable extension here:
    OUTPUT    ${MAKESPEC_OUTPUT_PATH}/dist${PI_NAME}/${PI_NAME}
    COMMAND   python ${BUILD_OPTIONS} ${PI_BUILD_SPEC}
    ARGS      ${MAKESPEC_FILENAME}
    DEPENDS   ${MAKESPEC_FILENAME}
    COMMENT   "Generating exe from spec file"
  )
# Ok I want the exe in the EXECUTABLE_OUTPUT_PATH:
  ADD_CUSTOM_COMMAND(
    OUTPUT    ${EXECUTABLE_OUTPUT_PATH}/${PI_TARGET_NAME}
    COMMAND   cmake -E copy_if_different
    ARGS      ${MAKESPEC_OUTPUT_PATH}/dist${PI_NAME}/${PI_NAME} ${EXECUTABLE_OUTPUT_PATH}/${PI_TARGET_NAME}
    DEPENDS   ${MAKESPEC_OUTPUT_PATH}/dist${PI_NAME}/${PI_NAME}
    COMMENT   "Copying exe in executable output path"
  )
  # Find all generated files:
  FILE(GLOB PI_GENERATED_FILES
    "${MAKESPEC_OUTPUT_PATH}/dist${PI_NAME}/*"
  )
  GET_DIRECTORY_PROPERTY(additional_make_clean_files ADDITIONAL_MAKE_CLEAN_FILES)

  ADD_CUSTOM_TARGET(${PI_TARGET_NAME}
    ALL
    COMMAND   cmake -E copy_directory ${MAKESPEC_OUTPUT_PATH}/dist${PI_NAME} ${LIBRARY_OUTPUT_PATH}
    DEPENDS   ${MAKESPEC_OUTPUT_PATH}/dist${PI_NAME}/${PI_NAME}
    COMMENT   "Making ${PI_NAME} target"
  )
  STRING(REPLACE ${MAKESPEC_OUTPUT_PATH}/dist${PI_NAME}
                 ${LIBRARY_OUTPUT_PATH}
                 pi_copied_files
                 "${PI_GENERATED_FILES}")
  #MESSAGE("${PI_GENERATED_FILES}")
  #MESSAGE("${pi_copied_files}")
  # TODO: there are some issues with make clean
  #SET_DIRECTORY_PROPERTIES(PROPERTIES
  #  ADDITIONAL_MAKE_CLEAN_FILES 
  #  "${additional_make_clean_files} ${EXECUTABLE_OUTPUT_PATH}/${PI_TARGET_NAME} ${PI_GENERATED_FILES} ${pi_copied_files}")
  #GET_DIRECTORY_PROPERTY(dummy ADDITIONAL_MAKE_CLEAN_FILES)
  #MESSAGE(${dummy})

  # FIXME: INSTALL command should be outside a UsePyInstaller.cmake file
  # install command should not be added unless user add them
  INSTALL(
# FIXME: lib are installer with execution bit set !
    PROGRAMS ${PI_GENERATED_FILES}
    DESTINATION lib
  )

  # Install exe in bin:
  INSTALL(
    PROGRAMS ${MAKESPEC_OUTPUT_PATH}/${PI_NAME}
    DESTINATION bin
  )

ENDMACRO(ADD_PI_EXECUTABLE)
