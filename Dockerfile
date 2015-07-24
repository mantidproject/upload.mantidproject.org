# CentOS 6.6 with apache and mod_wsgi
FROM centos:centos6.6
USER root

MAINTAINER Martyn Gigg <martyn.gigg@gmail.com>

# Install apache, mod_wsgi & git
RUN yum -y update  && yum -y install mod_wsgi git

# Apache config
COPY docker/etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf

# WSGI script and settings. This is referenced in httpd.conf
COPY scriptrepository_server.wsgi docker/var/www/wsgi_scripts/* /var/www/wsgi_scripts/
# Application
COPY scriptrepository_server/* /var/www/scriptrepository/application/scriptrepository_server/

# Create a fake remote and local git repository
RUN mkdir -p /var/www/scriptrepository/git && \
    git config --global user.name "Docker" && \
    git config --global user.email "a.b@domain.com"
# Setup a remote. It is left in a detached head state so that git push from the local works
RUN cd /var/www/scriptrepository/git && \
     mkdir remote && cd remote && \
     git init && \
     echo "README" > README.md && \
     git add . && \
     git commit -m"Initial commit" && \
     git checkout $(git rev-parse HEAD) && \
     chown -R apache:apache /var/www/scriptrepository/git/remote

# Clone to local and have apache own it
RUN cd /var/www/scriptrepository/git && \
    git clone /var/www/scriptrepository/git/remote local && \
    chown -R apache:apache /var/www/scriptrepository/git/local

# Run on port 80
EXPOSE 80

# Simple startup script to avoid some issues observed with container restart
ADD docker/run-httpd.sh /run-httpd.sh
RUN chmod -v +x /run-httpd.sh

CMD ["/run-httpd.sh"]
