#!/bin/bash
#$ -cwd

# set the appropriate home directory for JavaProjects
export JPHOME=${HOME}/Dropbox/JavaProjects

export CLASSPATH=${JPHOME}/lib/PilotView.jar

export JVMARGS="-Xms512M -Xmx14336M -Xnoclassgc"

echo java $JVMARGS -classpath $CLASSPATH PilotView.Main %1
java $JVMARGS -classpath $CLASSPATH PilotView.Main %1
