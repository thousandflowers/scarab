#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
mkdir -p "$DIR/output"

echo "Generazione CA per Scarab..."
openssl genrsa -out "$DIR/output/scarab-ca.key" 2048
openssl req -x509 -new -nodes -key "$DIR/output/scarab-ca.key" -sha256 -days 3650 -out "$DIR/output/scarab-ca.pem" -subj "/CN=Scarab Interceptor CA/O=Scarab/C=IT"

echo "Certificato CA generato in $DIR/output/scarab-ca.pem"

cat <<EOF > "$DIR/output/scarab.mobileconfig"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>PayloadCertificateFileName</key>
            <string>scarab-ca.pem</string>
            <key>PayloadContent</key>
            <data>
$(cat "$DIR/output/scarab-ca.pem" | grep -v "\-\-\-\-\-" | base64)
            </data>
            <key>PayloadDescription</key>
            <string>Aggiunge il certificato root Scarab CA per intercettazione traffico.</string>
            <key>PayloadDisplayName</key>
            <string>Scarab CA</string>
            <key>PayloadIdentifier</key>
            <string>com.scarab.ca</string>
            <key>PayloadType</key>
            <string>com.apple.security.root</string>
            <key>PayloadUUID</key>
            <string>12345678-1234-1234-1234-123456789012</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
        </dict>
    </array>
    <key>PayloadDisplayName</key>
    <string>Scarab Interceptor CA</string>
    <key>PayloadIdentifier</key>
    <string>com.scarab.profile</string>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>87654321-4321-4321-4321-210987654321</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>
EOF

echo "Profilo .mobileconfig generato in $DIR/output/scarab.mobileconfig"
