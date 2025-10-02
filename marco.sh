#!/bin/bash

marco(){
	export MARCO_DIR="$PWD"
	echo "saved directory: $MARCO_DIR"
}

polo(){
	if [ -n "$MARCO_DIR"]; then 
		cd "$MARCO_DIR" || return 
		echo "Moved back to : $MARCO_DIR"
	else
		echo "no directory saved ,run marco first"
	fi
}
