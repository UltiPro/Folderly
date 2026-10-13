FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
# Vite inlines this at build time, so it is baked into the JavaScript and
# cannot be changed with -e on a running container.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
COPY . .
# Not `npm run build`, which would run vue-tsc again. CI type-checks already.
RUN npm run build-only
FROM caddy:2-alpine
COPY --from=build /app/dist /srv
