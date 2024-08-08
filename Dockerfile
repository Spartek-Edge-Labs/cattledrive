FROM rockylinux:9

# drop in cattleDrive script
COPY cattleDrive.py /bin/cattleDrive
RUN chmod +x /bin/cattleDrive

# install yum and pip-based dependencies
RUN dnf -y install python3-pip wget yum-utils createrepo ansible-core skopeo rsync pigz && pip3 install jinja2 pyyaml

# helm
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# docker
RUN dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo && dnf -y install docker-ce-cli
