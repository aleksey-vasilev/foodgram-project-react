FROM nginx:1.22.1
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY openapi-schema.yml /usr/share/nginx/html
COPY redoc.html /usr/share/nginx/html