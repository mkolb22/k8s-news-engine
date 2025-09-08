FROM alpine:3.20

RUN apk add --no-cache lighttpd python3

RUN mkdir -p /var/www/htdocs \
    && mkdir -p /var/www/cgi-bin \
    && mkdir -p /var/log/lighttpd

COPY lighttpd.conf /etc/lighttpd/lighttpd.conf
COPY cgi-bin/publish /var/www/cgi-bin/publish
RUN chmod +x /var/www/cgi-bin/publish

EXPOSE 8080
CMD ["lighttpd", "-D", "-f", "/etc/lighttpd/lighttpd.conf"]
