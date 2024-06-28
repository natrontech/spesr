FROM golang:1.22-alpine AS backend-builder
WORKDIR /build
COPY pb/go.mod pb/go.sum pb/main.go ./
COPY pb/pkg ./pkg
RUN apk --no-cache add upx make git gcc libtool musl-dev ca-certificates dumb-init \
  && go mod tidy \
  && CGO_ENABLED=0 go build \
  && upx spesr

FROM node:lts-slim as ui-builder
WORKDIR /build
COPY ./sk/package*.json ./
RUN rm -rf ./node_modules
RUN rm -rf ./build
COPY ./sk .
RUN npm install --legacy-peer-deps
RUN npm run build

FROM alpine as runtime
WORKDIR /app/spesr
COPY --from=backend-builder /build/spesr /app/spesr/spesr
COPY ./pb/pb_migrations ./pb_migrations
COPY --from=ui-builder /build/build /app/spesr/pb_public
EXPOSE 8090
CMD ["/app/spesr/spesr","serve", "--http", "0.0.0.0:8090"]