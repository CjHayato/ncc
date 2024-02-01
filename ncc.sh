#/bin/bash
ncc_dir="/opt/ncc"
$(which python3) $ncc_dir/run_firefox.py
kill -9 $(ps -ef|awk '/firefox/&&/headless/&&!/awk/{print $2}')
