# 
Building a bare-metal Kubernetes cluster on Raspberry Pi computers

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


# Phase 0 — Verify tooling

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

# Phase 1 — Back up what you can't regenerate

```
kubectl get secret cloudflare-tunnel -n cloudflare -o yaml > $HOME\cloudflare-tunnel-backup.yaml
kubectl get configmap cloudflared-config -n cloudflare -o yaml > $HOME\cloudflared-config-backup.yaml
```

# Phase 2 — Clean the cluster

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

# Phase 3 — Clone and scaffold
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

# Phase 4 — Infrastructure files
- `.gitignore`
- `infrastructure/cloudflare/secret.yaml`
- `infrastructure/namespaces.yaml`
- `infrastructure/ssd-storageclass.yaml`
- `infrastructure/cloudflare/configmap.yaml`
- `infrastructure/cloudflare/tunnel.yaml`
- `infrastructure/cloudflare/secret.yaml`

# Phase 5 — Application code
This endpoint provides a **lightweight health check** that Kubernetes can use for **liveness** and **readiness probes** to verify the application is **running** and able to **serve traffic**, enabling **automated restarts** and **traffic routing decisions**.

```
@app.get("/health")
def health():
    return {"status": "ok"}
```

# Phase 6 — Application manifests
- `spaces/public/apps/helloapi/k8s/deployment.yaml`
- `spaces/public/apps/helloapi/k8s/service.yaml`
- `spaces/public/ingress/ingress.yaml`
- `argocd/apps/public.yaml`

# Phase 7 — GitHub Actions workflow
- `.github/workflows/deploy.yaml`

# Phase 8 — Apply infrastructure
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

# Phase 9 — Install ArgoCD

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

# Phase 10 — GHCR credentials

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

# Phase 11 — Seed the first image
```
echo $PAT | docker login ghcr.io -u adriensieg --password-stdin

docker buildx build --platform linux/arm64 `
  -t ghcr.io/adriensieg/public-helloapi:latest `
  --push spaces/public/apps/helloapi
```

Confirm it landed at `https://github.com/adriensieg?tab=packages`

# Phase 12 — Push and activate
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

# Phase 13 — Verify

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

# Phase 14 - How to modify the current app? The loop from now on

```
# edit spaces/public/apps/helloapi/app/main.py
git add .
git commit -m "feat: change message"
git push
```

# Phase 15 - Adding a second app to public
# Phase 16 - Adding a new workspace later


# Issues

The applicationset-controller crash

argocd-applicationset-controller is in CrashLoopBackOff with 36 restarts. You don't use ApplicationSets, so this doesn't block anything — but it's burning CPU on a Pi. Once the deployment works, either investigate it:


Why this happens and how to avoid it in future apps

Your ingress rewrites /helloapi/api/hello → /api/hello before it reaches FastAPI, so the app sees clean paths and doesn't know it's mounted under a prefix. Relative URLs in the frontend therefore break.

For anything more complex than this demo, set FastAPI's root_path so it generates correct URLs itself:

python
app = FastAPI(root_path="/helloapi")

That also fixes the Swagger docs at /helloapi/docs, which are currently broken for the same reason.