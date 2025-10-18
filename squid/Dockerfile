FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    squid \
    apache2-utils \
    && rm -rf /var/lib/apt/lists/*

# Create blocked page directory
RUN mkdir -p /var/www/html

EXPOSE 3128

CMD ["squid", "-N", "-d", "1"]
