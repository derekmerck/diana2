# docker build -t thomasyi17/diana2-full /path/toDockerfileFolder
FROM thomasyi17/diana2-gpg:latest

RUN apt-get install screen

RUN cd /opt/diana && git pull && git checkout Image_Analysis_Pipeline

RUN pip3 install -e ./package/