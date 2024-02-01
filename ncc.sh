#/bin/bash

basedir=/opt/ncc


cd $basedir
/bin/python3.9 $basedir/run_firefox.py
TARGET_PID=$(ps -ef|awk '/firefox/&&/headless/&&!/awk/{print $2}')
if [[ $TARGET_PID -gt 1 ]];then
  kill -9 $TARGET_PID
fi
exit 0
