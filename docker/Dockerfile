# CentOS 6.6 with apache and mod_wsgi
FROM centos:centos6.6
USER root

MAINTAINER Martyn Gigg <martyn.gigg@gmail.com>

# Install apache and mod_wsgi
RUN yum -y update  && yum -y install mod_wsgi

# Apache config
COPY etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf

# WSGI scripts. This is referenced in httpd.conf
COPY application/upload.wsgi /var/www/wsgi-scripts/upload.wsgi

# Directory for uploads
RUN mkdir /var/www/uploads && chown apache:apache /var/www/uploads

# Run on port 80
EXPOSE 80

# Simple startup script to avoid some issues observed with container restart
ADD run-httpd.sh /run-httpd.sh
RUN chmod -v +x /run-httpd.sh

CMD ["/run-httpd.sh"]
