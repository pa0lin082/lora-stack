FROM eclipse-mosquitto:latest

# Copy custom configuration file
COPY mosquitto.conf /mosquitto/config/mosquitto.conf

RUN mkdir -p /mosquitto/data /mosquitto/log && chown -R mosquitto:mosquitto /mosquitto/data /mosquitto/log

# Copy entrypoint
COPY entrypoint.sh /usr/bin/entrypoint.sh

# Ensure the script is executable
RUN chmod +x /usr/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]

# Define the command that the entrypoint will execute after creating the password file.
CMD ["/usr/sbin/mosquitto", "-c", "/mosquitto/config/mosquitto.conf"]
