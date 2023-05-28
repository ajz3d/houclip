#!/bin/sh
# Run Pylint over houclip package.
package="$HOUDINI_USER_PREF_DIR/packages/houclip"
pylint -ry "$package/scripts/python/houclip"
