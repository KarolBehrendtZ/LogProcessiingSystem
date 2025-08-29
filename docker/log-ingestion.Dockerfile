FROM golang:1.18 AS builder

WORKDIR /app

COPY services/log-ingestion/go.mod .
COPY services/log-ingestion/go.sum .
RUN go mod download

COPY services/log-ingestion/ .

RUN go build -o log-ingestion main.go

FROM gcr.io/distroless/base

COPY --from=builder /app/log-ingestion /usr/local/bin/log-ingestion

CMD ["log-ingestion"]