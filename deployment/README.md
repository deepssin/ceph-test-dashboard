# Deployment

Deploy the Ceph Test Dashboard with Podman locally, or on OpenShift.

## Prerequisites

### Podman (local)

- [Podman](https://podman.io/getting-started/installation) installed
- [Podman Compose](https://github.com/containers/podman-compose) installed

### OpenShift

See [`openshift/README.md`](openshift/README.md) for the full OpenShift flow (`deploy.sh`, config template, cert-manager).

---

## Podman Deployment

1. **Create the config file**

    If you haven't already configured the dashboard for local development, copy the template:

    ```sh
    mkdir -p ~/.config
    cp templates/config.ini.template ~/.config/ceph-test-dashboard.ini
    ```

    Edit `~/.config/ceph-test-dashboard.ini` and set your URLs:

    ```ini
    [paddles]
    base_url = http://paddles.example.com

    [pulpito]
    base_url = http://pulpito.example.com

    [nightly]
    run_user = jenkins-build

    [cache]
    # Report snapshots are shared across sessions for this many minutes.
    refresh_minutes = 60

    [release]
    branches = tentacle, squid, umbrella
    ```

2. **Build the container image**

    ```sh
    podman build --format docker -f deployment/Containerfile -t ceph-test-dashboard:latest .
    ```

3. **Create a data directory (persistent volume)**

    Podman mounts a host directory at `/var/lib/ceph-test-dashboard` (same path as OpenShift). Create it once:

    ```sh
    mkdir -p ./ceph-test-dashboard-data
    ```

4. **Start the service**

    ```sh
    podman-compose -f deployment/podman-compose.yaml up -d
    ```

    To use a custom config file path, port, or data directory:

    ```sh
    CONFIG_FILE=/path/to/config.ini \
    DATA_DIR=/path/to/ceph-test-dashboard-data \
    DASHBOARD_PORT=9000 \
      podman-compose -f deployment/podman-compose.yaml up -d
    ```

5. **Verify the deployment**

    ```sh
    podman-compose -f deployment/podman-compose.yaml ps
    ```

    The container should show "Up" status.

6. **Access the dashboard**

    Open your browser at `http://localhost:8501` (or the custom port you set).

    On first start the app initializes the data volume (marker file) and writes
    `mail-state.sqlite` there when outbound mail is enabled.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_FILE` | `~/.config/ceph-test-dashboard.ini` | Path to the config file on the host |
| `DATA_DIR` | `./ceph-test-dashboard-data` | Host dir mounted at `/var/lib/ceph-test-dashboard` |
| `DASHBOARD_PORT` | `8501` | Host port to expose the dashboard on |

### Managing the Service

Stop:

```sh
podman-compose -f deployment/podman-compose.yaml down
```

View logs:

```sh
podman-compose -f deployment/podman-compose.yaml logs -f
```

---

## OpenShift Deployment

OpenShift manifests and the deploy script live under [`openshift/`](openshift/) (`deploy.sh` + config template + `envsubst`).

Quick start:

```sh
cd deployment/openshift
cp ./dashboard.config.tmpl ./dashboard.config
# edit dashboard.config — set namespace, image, route host, paddles/pulpito URLs
chmod +x ./deploy.sh
./deploy.sh --dashboard-config ./dashboard.config
```

Without cert-manager (use the default router certificate):

```sh
./deploy.sh --dashboard-config ./dashboard.config --skip-cert
```

Full details: [`openshift/README.md`](openshift/README.md).
