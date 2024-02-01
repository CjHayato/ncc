#/bin/bash
cd /opt/ncc
echo /bin/python3 /opt/ncc/run_firefox.py
kill -9 $(ps -ef|awk '/firefox/&&/headless/&&!/awk/{print $2}')
