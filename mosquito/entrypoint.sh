#!/bin/sh

# Shutdown on error
set -e

# Check if MOSQUITTO_USERNAME and MOSQUITTO_PASSWORD environment variables are defined
if [ -z "$MOSQUITTO_USERNAME" ] || [ -z "$MOSQUITTO_PASSWORD" ]; then
  echo "ERRO: As variáveis de ambiente MOSQUITTO_USERNAME e MOSQUITTO_PASSWORD precisam ser definidas."
  exit 1
fi

# Create password file
mosquitto_passwd -b -c /mosquitto/config/password_file "$MOSQUITTO_USERNAME" "$MOSQUITTO_PASSWORD"

# Define "mosquitto" as owner of the password file
chown mosquitto:mosquitto /mosquitto/config/password_file

# Passes execution to the container's original command (starts Mosquitto)
# "$@" represents all arguments passed to the script, which in our case
# will be the command to start the broker defined in the Dockerfile.
exec "$@"