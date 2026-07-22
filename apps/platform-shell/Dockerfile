FROM node:24.13.1-alpine@sha256:4f696fbf39f383c1e486030ba6b289a5d9af541642fc78ab197e584a113b9c03 AS build
WORKDIR /workspace

COPY package.json package-lock.json ./
COPY apps/platform-shell/package.json apps/platform-shell/package.json
COPY apps/projects/frontend/package.json apps/projects/frontend/package.json
COPY apps/service-desk/frontend/package.json apps/service-desk/frontend/package.json
COPY contracts/generated contracts/generated
COPY packages/frontend packages/frontend
# npm lockfiles produced on Windows omit Rolldown's Linux optional native
# package; install the pinned Alpine binding explicitly without mutating the
# committed lockfile.
RUN npm ci \
    && npm install --no-save --package-lock=false @rolldown/binding-linux-x64-musl@1.1.4

COPY apps/platform-shell apps/platform-shell
COPY apps/projects/frontend apps/projects/frontend
COPY apps/service-desk/frontend apps/service-desk/frontend
ARG VITE_API_BASE_URL=/api/projects/v1
ARG VITE_SERVICE_DESK_API_BASE_URL=/api/service-desk/v1
ARG VITE_ACCESS_API_BASE_URL=/api/access/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_SERVICE_DESK_API_BASE_URL=$VITE_SERVICE_DESK_API_BASE_URL \
    VITE_ACCESS_API_BASE_URL=$VITE_ACCESS_API_BASE_URL
RUN npm run build --workspace=@prom/platform-shell

FROM nginx:1.30.3-alpine@sha256:0d3b80406a13a767339fbe2f41406d6c7da727ab89cf8fae399e81f780f814d1 AS runtime
COPY apps/platform-shell/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/platform-shell/dist /usr/share/nginx/html
RUN chown -R nginx:nginx \
    /etc/nginx/conf.d \
    /usr/share/nginx/html \
    /var/cache/nginx \
    /var/log/nginx \
    /var/run
USER nginx
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=10 CMD ["wget", "-q", "--spider", "http://127.0.0.1/healthz"]
