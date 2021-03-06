file(GLOB_RECURSE AVANGO_LOD_PYTHON_SRC RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
    *.cpp
    *.hpp
)

ADD_LIBRARY( _lod SHARED 
  ${AVANGO_LOD_PYTHON_SRC}
)

set_target_properties( _lod
  PROPERTIES LIBRARY_OUTPUT_DIRECTORY
  ${CMAKE_SOURCE_DIR}/lib/avango/gua/lod
)

TARGET_LINK_LIBRARIES( _lod avango_lod)
SET_TARGET_PROPERTIES( _lod PROPERTIES PREFIX "")

###############################################################################
# install modules
###############################################################################
IF (MSVC)
  post_build_install_target(_lod
    ${AVANGO_INSTALL_DIRECTORY}/python3.5/avango/gua/lod/_lod.pyd)
ELSEIF (UNIX)
  post_build_install_target(_lod
    ${AVANGO_INSTALL_DIRECTORY}/python3.5/avango/gua/lod/_lod.so)
ENDIF (MSVC)

###############################################################################
# install utilities
###############################################################################
COPY_PYTHON_FILES_INTO_DIRECTORY(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${AVANGO_INSTALL_DIRECTORY}/python3.5/avango/gua/lod
    _lod
)
