FROM python:3

WORKDIR /usr/src/app

# Replace 1000 with your user / group id
#RUN whoami
#RUN echo cut -d: -f1 /etc/passwd
#RUN export uid=1000 gid=1000 uname=root && \
#    mkdir -p /home/${uname} && \
#    mkdir -p /etc/sudoers.d/ && \
#    echo "developer:x:${uid}:${gid}:Developer,,,:/home/${uname}:/bin/bash" >> /etc/passwd && \
#    echo "developer:x:${uid}:" >> /etc/group && \
#    echo "developer ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/${uname} && \
#    chmod 0440 /etc/sudoers.d/${uname} && \
#    chown ${uid}:${gid} -R /home/${uname}
#USER python


RUN pip3.6 install netCDF4
RUN pip3.6 install pyyaml

# Required by the ncml writer
RUN pip3.6 install lxml

# Required by continuously run the converter during development
# RUN pip3.6 install watchdog


RUN apt update
#RUN apt install -y netcdf-bin
RUN apt install -y ncview

