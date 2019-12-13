"""Settings for the kytos/storehouse NApp."""

# Where to store data: "filesystem" (default) or "etcd" (requires a
# running server)
BACKEND = "filesystem"
# Path to serialize the objects, relative to a venv, if it exists.
CUSTOM_DESTINATION_PATH = "/var/tmp/kytos/storehouse"
# Path to store lock files, relative to a venv, if it exists.
CUSTOM_LOCK_PATH = "/var/tmp/lock"
