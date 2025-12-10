FROM nginx:1.27-alpine

# Copy static assets
COPY index.html /usr/share/nginx/html/index.html
COPY script.js /usr/share/nginx/html/script.js
COPY styles.css /usr/share/nginx/html/styles.css

EXPOSE 3000

# Use default nginx config serving /usr/share/nginx/html on port 80
CMD ["nginx", "-g", "daemon off;"]


