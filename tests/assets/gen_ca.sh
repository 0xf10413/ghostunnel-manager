#! /bin/sh
# Regenerates the CA and server/client certs

# Generate CA
echo "== Generating ca certs =="
openssl genrsa -out ca.key 2048
openssl req -new -key ca.key -out ca.csr \
    -subj "/CN=root/C=FR/ST=Rhône/L=Lyon/O=Organization/OU=Unit/"
openssl x509 -req -sha256 -days 3650 \
    -in ca.csr -signkey ca.key -out ca.pem \
    -extfile ca.ext -extensions ca


# Generate server certs
echo "== Generating server certs =="
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
    -subj "/CN=localhost/C=FR/ST=Rhône/L=Lyon/O=Organization/OU=Unit/"
openssl x509 -req -sha256 -days 3650 \
    -in server.csr -CA ca.pem -CAkey ca.key -out server.pem \
    -CAcreateserial \
    -extfile ca.ext -extensions server


# Generates client certs
echo "== Generating client certs =="
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr \
    -subj "/CN=localhost/C=FR/ST=Rhône/L=Lyon/O=Organization/OU=Unit/"
openssl x509 -req -sha256 -days 3650 \
    -in client.csr -CA ca.pem -CAkey ca.key -out client.pem \
    -CAcreateserial \
    -extfile ca.ext -extensions client
