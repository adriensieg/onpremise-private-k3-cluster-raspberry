# 
Building a bare-metal Kubernetes cluster on Raspberry Pi computers

# - Boostrap from scratch
    - Phase 0 — Verify tooling
    - Phase 1 — Back up what you can't regenerate
    - Phase 2 — Clean the cluster
    - Phase 3 — Clone and scaffold
    - Phase 4 — Infrastructure files
    - Phase 5 — Application code
    - Phase 6 — Application manifests
    - Phase 7 — GitHub Actions workflow
    - Phase 8 — Apply infrastructure
    - Phase 9 — Cloudflare DNS
    - Phase 10 — Install ArgoCD
    - Phase 11 — GHCR credentials
    - Phase 12 — Seed the first image
    - Phase 13 — Push and activate
    - Phase 14 — Verify
# - Adding a second app to an existing workspace

# Boostrap from scratch

### Phase 0 — Verify tooling

On our local Windows machine:

```
kubectl version --client
docker version
git --version
argocd version --client
```

If `argocd` fails:

```
winget install ArgoProj.ArgoCD
```

Verify cluster access and inventory:

```
kubectl get nodes
kubectl get namespaces
kubectl get pods -A
```

Both nodes Ready. Note which namespaces are yours vs. system.

### Phase 1 — Back up what you can't regenerate

```
kubectl get secret cloudflare-tunnel -n cloudflare -o yaml > $HOME\cloudflare-tunnel-backup.yaml
kubectl get configmap cloudflared-config -n cloudflare -o yaml > $HOME\cloudflared-config-backup.yaml
```

### Phase 2 — Clean the cluster

```
delete namespace public mcd perso hackaton techie apps
```

Wait until gone:
```
kubectl get namespaces
```

**Keep**: `kube-system`, `kube-public`, `kube-node-lease`, `default`, `ingress-nginx`, `cloudflare`.

Verify infrastructure survived:

```
kubectl get pods -n ingress-nginx
kubectl get pods -n cloudflare
```

Both Running.

### Phase 3 — Clone and scaffold
```
cd $HOME
git clone https://github.com/adriensieg/onpremise-private-k3-cluster-raspberry.git
cd onpremise-private-k3-cluster-raspberry

mkdir -p .github/workflows
mkdir -p argocd/apps
mkdir -p infrastructure/cloudflare
mkdir -p spaces/public/apps/helloapi/app/static
mkdir -p spaces/public/apps/helloapi/k8s
mkdir -p spaces/public/ingress
```

Target structure:
```
onpremise-private-k3-cluster-raspberry/
├── .gitignore
├── .github/workflows/deploy.yaml
├── argocd/apps/public.yaml
├── infrastructure/                    ← applied by hand
│   ├── namespaces.yaml
│   ├── ssd-storageclass.yaml
│   └── cloudflare/
│       ├── configmap.yaml
│       ├── secret.yaml                ← gitignored
│       ├── secret.yaml.example
│       └── tunnel.yaml
└── spaces/public/                     ← managed by ArgoCD
    ├── apps/helloapi/
    │   ├── app/
    │   │   ├── main.py
    │   │   ├── requirements.txt
    │   │   └── static/index.html
    │   ├── Dockerfile
    │   └── k8s/
    │       ├── deployment.yaml
    │       └── service.yaml
    └── ingress/ingress.yaml
```

### Phase 4 — Infrastructure files
- `.gitignore`
- `infrastructure/cloudflare/secret.yaml`
- `infrastructure/namespaces.yaml`
- `infrastructure/ssd-storageclass.yaml`
- `infrastructure/cloudflare/configmap.yaml`
- `infrastructure/cloudflare/tunnel.yaml`
- `infrastructure/cloudflare/secret.yaml`

### Phase 5 — Application code
This endpoint provides a **lightweight health check** that Kubernetes can use for **liveness** and **readiness probes** to verify the application is **running** and able to **serve traffic**, enabling **automated restarts** and **traffic routing decisions**.

```
@app.get("/health")
def health():
    return {"status": "ok"}
```

### Phase 6 — Application manifests
- `spaces/public/apps/helloapi/k8s/deployment.yaml`
- `spaces/public/apps/helloapi/k8s/service.yaml`
- `spaces/public/ingress/ingress.yaml`
- `argocd/apps/public.yaml`

### Phase 7 — GitHub Actions workflow
- `.github/workflows/deploy.yaml`

### Phase 8 — Apply infrastructure
Order matters — namespaces first, secret before the deployment that mounts it:

```
kubectl apply -f infrastructure/namespaces.yaml
kubectl apply -f infrastructure/ssd-storageclass.yaml
kubectl apply -f infrastructure/cloudflare/secret.yaml
kubectl apply -f infrastructure/cloudflare/configmap.yaml
kubectl apply -f infrastructure/cloudflare/tunnel.yaml
```

Restart the tunnel to pick up the configmap:

```
kubectl rollout restart deployment cloudflared -n cloudflare
kubectl rollout status deployment cloudflared -n cloudflare
```

Verify:
```
kubectl get pods -n cloudflare
kubectl logs -n cloudflare -l app=cloudflared --tail=30
```
Logs should show the tunnel registering without errors.

No DNS step needed — `devailab.work` is already in Cloudflare and live.

### Phase 9 — Install ArgoCD

```
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=Ready pod --all -n argocd --timeout=300s
```

Get the initial password:

```
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_)) }
```

In a second PowerShell window, leave running:
```
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Back in the first window:
```
argocd login localhost:8080 --username admin --password <PASTE> --insecure
argocd account update-password
```

### Phase 10 — GHCR credentials

Create a PAT at https://github.com/settings/tokens → classic → scope read:packages → no expiration.

```
$PAT = "ghp_PASTE_HERE"

kubectl create secret docker-registry ghcr-secret `
  --docker-server=ghcr.io `
  --docker-username=adriensieg `
  --docker-password=$PAT `
  --docker-email=your@email.com `
  -n public
```

Verify:
```
kubectl get secret ghcr-secret -n public
```

### Phase 11 — Seed the first image
```
echo $PAT | docker login ghcr.io -u adriensieg --password-stdin

docker buildx build --platform linux/arm64 `
  -t ghcr.io/adriensieg/public-helloapi:latest `
  --push spaces/public/apps/helloapi
```

Confirm it landed at `https://github.com/adriensieg?tab=packages`

### Phase 12 — Push and activate
```
git add .
git commit -m "feat: initial CICD setup with helloapi"
git branch -M master
git push -u origin master
```

Register with ArgoCD:
```
argocd repo add https://github.com/adriensieg/onpremise-private-k3-cluster-raspberry
kubectl apply -f argocd/apps/public.yaml
argocd app sync public
```

### Phase 13 — Verify

```
argocd app list
kubectl get pods -n public
kubectl get svc -n public
kubectl get ingress -n public
kubectl logs -n public -l app=helloapi
```

Pod Running, ArgoCD app Synced / Healthy. Then open: `https://devailab.work/helloapi`

If you get a 502:

```
kubectl describe ingress public-ingress -n public
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=50
```

### Phase 14 - How to modify the current app? The loop from now on

```
# edit spaces/public/apps/helloapi/app/main.py
git add .
git commit -m "feat: change message"
git push
```

# Adding a second app to an existing workspace

### 0. Layout

```
spaces/public/apps/clotilde/
├── app/
│   ├── main.py
│   ├── requirements.txt
│   └── static/index.html
├── Dockerfile
└── k8s/
    ├── deployment.yaml
    └── service.yaml
```
Plus one edit to `spaces/public/ingress/ingress.yaml`.


### 1. Scaffold

```
mkdir -p spaces/public/apps/clotilde/app/static
mkdir -p spaces/public/apps/clotilde/k8s

# app/requirements.txt
# app/main.py
# app/static/index.html
# Dockerfile
# k8s/deployment.yaml
# k8s/service.yaml
```

`Dockerfile`
```
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Add ingress rule

Edit `spaces/public/ingress/ingress.yaml`, add a second path under the same host:

```
- path: /clotilde(/|$)(.*)
  pathType: ImplementationSpecific
  backend:
    service:
      name: clotilde
      port:
        number: 8000
```

### 4. Seed the first image

The manifest points at an image that doesn't exist yet. Build and push it once by hand:

```
docker buildx build --platform linux/arm64 `
  -t ghcr.io/adriensieg/public-clotilde:latest `
  --push spaces/public/apps/clotilde

docker buildx build --platform linux/arm64 -t ghcr.io/adriensieg/public-clotilde:latest --push spaces/public/apps/clotilde
```

Then link the package to the repo at https://github.com/users/adriensieg/packages/container/public-clotilde/settings → Manage Actions access → add repo with Write. Otherwise the first Actions build hits 403.

[](/static-tutorial/docker-error-auth.png)

The package public-clotilde was created by your manual docker push in Step 9, so it's owned by your account with no link to the repo. GITHUB_TOKEN is repo-scoped, so it's denied. This is Step 9's linking note that got skipped.

[](/static-tutorial/solution-docker-error-auth.png)

##### Fix
- Go to `https://github.com/users/adriensieg/packages/container/public-clotilde/settings`
- Scroll to Manage Actions access → Add Repository → select onpremise-private-k3-cluster-raspberry → set role to Write.

##### Re-run
- Browser: Actions tab → the failed run → Re-run jobs → Re-run failed jobs.
- It reuses the same commit; nothing to push. The build succeeds, rewrites the tag, commits back — then git pull locally to pick up the bot commit.
### 5. Push

```
git pull
git add .
git commit -m "feat: add clotilde notes app"
git push
```

Actions builds it, rewrites the tag, commits back. ArgoCD syncs within ~3 min — no new ArgoCD config needed, it already watches `spaces/public`.

### 6. Verify

```
kubectl get pods -n public -l app=clotilde -w
```

Then open https://devailab.work/clotilde.

# Adding a new workspace
A new workspace needs the five home-network steps, not just app files. URL will be `https://private.devailab.work/adrien`

### Step 0: Layout

```
spaces/private/
├── apps/adrien/
│   ├── app/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── static/index.html
│   ├── Dockerfile
│   └── k8s/
│       ├── deployment.yaml
│       └── service.yaml
└── ingress/ingress.yaml
```

### Step 1 — Scaffold

```
mkdir -p spaces/private/apps/adrien/app/static
mkdir -p spaces/private/apps/adrien/k8s
mkdir -p spaces/private/ingress
```

### Step 2 — Add namespace

Append to `infrastructure/namespaces.yaml`:
```
---
apiVersion: v1
kind: Namespace
metadata:
  name: private
```

Apply:
```
kubectl apply -f infrastructure/namespaces.yaml
```

### Step 3 — Cloudflare tunnel route

Add the hostname to `infrastructure/cloudflare/configmap.yaml`, above the http_status:404 line:

```
      - hostname: private.devailab.work
        service: http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80
```
Apply and restart:
```
kubectl apply -f infrastructure/cloudflare/configmap.yaml
kubectl rollout restart deployment cloudflared -n cloudflare
```

### Step 4 — Cloudflare DNS

Dashboard → add CNAME: name private, target <tunnel-id>.cfargotunnel.com, proxied.

### Step 5 — Pull secret in new namespace

```
$PAT = "ghp_PASTE_HERE"
kubectl create secret docker-registry ghcr-secret `
  --docker-server=ghcr.io `
  --docker-username=adriensieg `
  --docker-password=$PAT `
  --docker-email=your@email.com `
  -n private

We can get your GitHub Personal Access Token (PAT) https://github.com/settings/tokens

kubectl create secret docker-registry ghcr-secret --docker-server=ghcr.io --docker-username=adriensieg --docker-password=$PAT --docker-email=adriensieg@hotmail.fr -n private
```

Build into an ARM64 Docker image to GHCR

```
cd C:\Users\cloti\Desktop\HandsOn\onpremise-private-k3-cluster-raspberry

docker buildx build --platform linux/arm64 -t ghcr.io/adriensieg/private-adrien:latest --push spaces/private/apps/adrien
```

Then link it: `https://github.com/users/adriensieg/packages/container/private-adrien/settings` → Manage Actions access → add repo with Write. Skips the 403 on first Actions build.

### Step 7 — Register ArgoCD app + push

```
kubectl apply -f argocd/apps/private.yaml

git pull
git add .
git commit -m "feat: add private workspace with adrien app"
git push
```

### Step 8 — Verify

```
kubectl get pods -n private -w
```
Then open `https://private.devailab.work/adrien`

# TO COME
### What i have now? 
1. https://devailab.work/helloapi
2. https://devailab.work/clotilde
3. https://perso.devailab.work/adrien

### What i will have? 
1. Have a home page > https://devailab.work/
2. Have a new app in the default space > https://devailab.work/
3. Have a new space > https://private.devailab.work/
4. Have a new space with new app > https://private.devailab.work/helloapi


# Current issues
The applicationset-controller crash

argocd-applicationset-controller is in CrashLoopBackOff with 36 restarts. You don't use ApplicationSets, so this doesn't block anything — but it's burning CPU on a Pi. Once the deployment works, either investigate it:


Why this happens and how to avoid it in future apps

Your ingress rewrites /helloapi/api/hello → /api/hello before it reaches FastAPI, so the app sees clean paths and doesn't know it's mounted under a prefix. Relative URLs in the frontend therefore break.

For anything more complex than this demo, set FastAPI's root_path so it generates correct URLs itself:

python
app = FastAPI(root_path="/helloapi")

That also fixes the Swagger docs at /helloapi/docs, which are currently broken for the same reason.