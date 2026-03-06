FROM node:18-alpine
WORKDIR /app
COPY frontend/ .
RUN npm install
RUN ./node_modules/.bin/vite build
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]