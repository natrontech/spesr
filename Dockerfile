FROM golang:1.27-alpine AS backend-builder
WORKDIR /build
COPY pb/go.mod pb/go.sum pb/main.go ./
COPY pb/pkg ./pkg
RUN apk --no-cache add upx make git gcc libtool musl-dev ca-certificates dumb-init \
  && go mod download \
  && CGO_ENABLED=0 go build \
  && upx spesr

FROM node:22-slim AS ui-builder
WORKDIR /build
COPY ./sk/package*.json ./
COPY ./sk .
RUN npm ci --legacy-peer-deps
RUN npm run build

FROM alpine AS runtime
RUN addgroup -S spesr && adduser -S spesr -G spesr -h /app/spesr
WORKDIR /app/spesr
COPY --from=backend-builder /build/spesr /app/spesr/spesr
COPY ./pb/pb_migrations ./pb_migrations
COPY --from=ui-builder /build/build /app/spesr/pb_public
RUN chown -R spesr:spesr /app/spesr
USER spesr
EXPOSE 8090
CMD ["/app/spesr/spesr","serve", "--http", "0.0.0.0:8090"]
