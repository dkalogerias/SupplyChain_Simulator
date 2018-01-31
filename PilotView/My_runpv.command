#!/bin/bash
#$ -cwd

# Make sure the directory is the current one!
# -------------------------------------------
cd -- "$(dirname "$0")"

# Not needed at this point
# ------------------------
# set the appropriate home directory for JavaProjects
#export JPHOME=${HOME}/Dropbox/JavaProjects
#export CLASSPATH=PilotView.jar

export JVMARGS="-Xms512M -Xmx14336M -Xnoclassgc"

echo java $JVMARGS -classpath PilotView.jar PilotView.Main %1
java $JVMARGS -classpath PilotView.jar PilotView.Main %1
