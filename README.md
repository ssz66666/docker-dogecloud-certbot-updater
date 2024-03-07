# docker-dogecloud-certbot-updater

Docker image for periodically uploading renewed SSL certificates to [DogeCloud CDN](https://www.dogecloud.com/). Written to be used with [docker-nginx-certbot](https://github.com/JonasAlfredsson/docker-nginx-certbot/) by [@JonasAlfredsson](https://github.com/JonasAlfredsson)

## Usage

Sample config for a simple static blog, with free SSL certificate from [Let's Encrypt](https://letsencrypt.org/), configured to use DogeCloud CDN.

- Install Docker on your server, e.g. by following [the offical instruction](https://docs.docker.com/desktop/install/linux-install/).
- Prepare your website and the configuration files.
- Get it up and running with
```
docker compose up -d
```

## Sample Config

### Directory Structure
```
├── public
│   ├── css
│   │   ├── **/*.css
│   ├── images
│   ├── js
│   ├── index.html
├── user_conf.d
│   ├── example.com.conf
│   ├── test.example.com.conf
├── cert-update.env
├── docker-compose.yml
├── nginx-certbot.env
```

### nginx-certbot.env
```
### refer to https://github.com/JonasAlfredsson/docker-nginx-certbot
# Required
CERTBOT_EMAIL=john.smith@example.com
```

### cert-update.env
```
## Put your API credentials here
## you can find it on https://console.dogecloud.com/user/keys
DOGECLOUD_ACCESSKEY=<Your DogeCloud AccessKey>
DOGECLOUD_SECRETKEY=<Your DogeCloud SecretKey>

## assuming Let's Encrypt SSL certificates are stored in the default path /etc/letsencrypt/live/
## multiple domains are delimited by commas
DOMAIN_CERT_PAIRS=example.com:/etc/letsencrypt/live/example.com/,test.example.com:/etc/letsencrypt/live/test.example.com/
```

### docker-compose.yml

```
services:
  nginx:
    image: jonasal/nginx-certbot:latest
    restart: unless-stopped
    env_file:
      - ./nginx-certbot.env
    ports:
      - 80:80
      - 443:443
    volumes:
      - nginx_secrets:/etc/letsencrypt
      - ./user_conf.d:/etc/nginx/user_conf.d
      - ./public:/usr/share/nginx/html:ro

  dogecloud-cert-updater:
    image: ssz66666/docker-dogecloud-certbot-updater:latest
    restart: unless-stopped
    env_file:
      - ./cert-update.env
    volumes:
      - nginx_secrets:/etc/letsencrypt:ro

volumes:
  nginx_secrets:
```
