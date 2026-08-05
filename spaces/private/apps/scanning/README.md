# Scanning app — private workspace

Mobile-first FastAPI CRUD app, served at `https://private.devailab.work/scanning`.

## Layout

```
spaces/private/
├── apps/scanning/
│   ├── app/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── templates/index.html
│   │   └── static/
│   │       ├── script.js
│   │       ├── style.css
│   │       ├── sw.js
│   │       └── icons/
│   ├── Dockerfile
│   └── k8s/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── argocd-application.yaml
└── ingress/ingress.yaml
```

## Key design points

- App runs with `ROOT_PATH=/scanning`; every asset, API, and manifest URL is prefixed accordingly.
- Ingress is **passthrough** (no rewrite): `/scanning/...` is forwarded unchanged and the app serves it.
- Health endpoint is at `/scanning/health` inside the pod — matches the probes.
- Data persists to `/data/data.txt` on an `emptyDir` volume (survives container restart, not pod reschedule — swap for a PVC if you need durability).

## Deploy

### 1. Namespace
Append to `infrastructure/namespaces.yaml`:
```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: private
```
```bash
kubectl apply -f infrastructure/namespaces.yaml
```

### 2. Cloudflare tunnel route
In `infrastructure/cloudflare/configmap.yaml`, above the `http_status:404` line:
```yaml
      - hostname: private.devailab.work
        service: http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80
```
```bash
kubectl apply -f infrastructure/cloudflare/configmap.yaml
kubectl rollout restart deployment cloudflared -n cloudflare
```

### 3. DNS
Cloudflare dashboard → CNAME: name `private`, target `<tunnel-id>.cfargotunnel.com`, proxied.

### 4. GHCR pull secret
```powershell
$PAT = "ghp_PASTE_HERE"
kubectl create secret docker-registry ghcr-secret --docker-server=ghcr.io --docker-username=adriensieg --docker-password=$PAT --docker-email=adriensieg@hotmail.fr -n private
```

### 5. Build & push (ARM64)
```powershell
cd C:\Users\cloti\Desktop\HandsOn\onpremise-private-k3-cluster-raspberry
docker buildx build --platform linux/arm64 -t ghcr.io/adriensieg/private-scanning:latest --push spaces/private/apps/scanning
```
Then link the package to the repo (Package settings → Manage Actions access → add repo, Write).

https://github.com/users/adriensieg/packages/container/private-scanning/settings

### 6. Ingress
```bash
kubectl apply -f spaces/private/ingress/ingress.yaml
```

### 7. Register with ArgoCD + push
```
kubectl apply -f argocd/apps/private.yaml

git pull
git add .
git commit -m "feat: add private workspace with adrien app"
git push
```

### 8. Verify
```bash
kubectl get pods -n private -w
```
Then open `https://private.devailab.work/scanning`.

## Troubleshooting

- **Pod CrashLoopBackOff / probe failing**: check the probe hits `/scanning/health`, not `/health`. `kubectl logs -n private deploy/scanning`.
- **404 at /scanning**: confirm the ingress is passthrough (no `rewrite-target` annotation) and `ROOT_PATH=/scanning` is set on the container.
- **Assets 404 but page loads**: the `<base href="/scanning/">` tag or `ROOT_PATH` is wrong — every static URL must start with `/scanning/`.
- **ImagePullBackOff**: `ghcr-secret` missing in the `private` namespace, or the package isn't linked to the repo.
