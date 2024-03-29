#!/bin/sh

#user paths
USER_GEDIT_PLUGINS_FOLDER="$HOME/.local/share/gedit/plugins"
USER_ICONS_FOLDER="$HOME/.local/share/icons"

#root paths
ROOT_GEDIT_PLUGINS_FOLDER="/usr/lib/gedit/plugins"
ROOT_GEDIT_SCHEMAS_FOLDER="/usr/share/glib-2.0/schemas"
ROOT_GEDIT_PLUGINS_DATA_FOLDER="/usr/share/gedit/plugins/haxeide"
ROOT_ICONS_FOLDER="/usr/share/icons"

remove_file() 
{
	if [ -f $2/$1 ]; then
		echo "Removing file: $1, from: $2"
		rm $2/$1 || exit 1
	fi
}

remove_folder() 
{
	if [ -d $2/$1 ]; then
		echo "Removing folder: $1, from: $2"
		rm -r $2/$1 || exit 1
	fi
}

echo "*** Uninstalling haXe IDE plugin for gedit 3.x ***"
if [ `whoami` = 'root' ]; then
	remove_file 'haxeide.plugin' "$ROOT_GEDIT_PLUGINS_FOLDER"
	remove_folder 'haxeide' "$ROOT_GEDIT_PLUGINS_FOLDER"
	remove_folder 'haxeide/ui' "$ROOT_GEDIT_PLUGINS_DATA_FOLDER"
	remove_folder 'haxeide/icons' "$ROOT_GEDIT_PLUGINS_DATA_FOLDER"
	remove_folder 'haxeide/scripts' "$ROOT_GEDIT_PLUGINS_DATA_FOLDER"
	echo "Recompiling: glib-compile-schemas"
	glib-compile-schemas "$ROOT_GEDIT_SCHEMAS_FOLDER"
else
	remove_file 'haxeide.plugin' "$USER_GEDIT_PLUGINS_FOLDER"
	remove_folder 'haxeide' "$USER_GEDIT_PLUGINS_FOLDER"
fi

echo "Done uninstalling.\n"
