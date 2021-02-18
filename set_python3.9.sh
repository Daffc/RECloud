apt update && apt upgrade 
apt install wget build-essential libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev 
wget https://www.python.org/ftp/python/3.9.1/Python-3.9.1.tgz -P/tmp/
tar xzf /tmp/Python-3.9.1.tgz -C /tmp/
cd /tmp/Python-3.9.1
./configure --enable-optimizations
make altinstall 

cd ..
rm -r Python-3.9.1*
