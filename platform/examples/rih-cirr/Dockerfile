# docker build -t thomasyi17/diana2-gpg /path/to/Dockerfile
# Missing gpg key fix
FROM derekmerck/diana2:latest

RUN sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 112695A0E562B32A

RUN sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 648ACFD622F3D138

RUN apt-get update && apt-get install vim

RUN cd /opt/diana && git pull && git checkout Image_Analysis_Pipeline

