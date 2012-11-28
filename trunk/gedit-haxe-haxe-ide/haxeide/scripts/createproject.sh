#!/bin/sh
#
# Installs the haxe code completion plugin for user or root

#install a folder
copy_folder() 
{
	echo "Adding folder $1 to $2"
	cp -r "$1" "$2" || exit 1
	mv $2/$1 $2/$3
}

if [ `whoami` = 'root' ]; then
	copy_folder $1'project' $2 $3
else
	copy_folder $1'project' $2 $3
fi
