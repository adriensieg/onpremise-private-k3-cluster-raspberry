
## Layout

```
spaces/techie/
├── apps/twillio-gtw/
│   ├── app/
│   │   ├── main.py
│   │   ├── lib/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── prompts.py
│   │   └── requirements.txt
│   ├── Dockerfile
│   └── k8s/
│       ├── deployment.yaml
│       └── service.yaml
└── ingress/ingress.yaml
```

### Scaffold

```
mkdir -p spaces/techie/apps/twillio-gtw/app
mkdir -p spaces/techie/apps/twillio-gtw/k8s
mkdir -p spaces/techie/ingress
```

### Add namespace

Append to `infrastructure/namespaces.yaml`:
```
---
apiVersion: v1
kind: Namespace
metadata:
  name: techie
```

Apply:
```
kubectl apply -f infrastructure/namespaces.yaml
```

### Step 3 — Cloudflare tunnel route

Add the hostname to `infrastructure/cloudflare/configmap.yaml`, above the http_status:404 line:

```
      - hostname: techie.devailab.work
        service: http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80
```
Apply and restart:
```
kubectl apply -f infrastructure/cloudflare/configmap.yaml
kubectl rollout restart deployment cloudflared -n cloudflare
```

### Step 4 — Cloudflare DNS

Dashboard → add CNAME: name techie, target <tunnel-id>.cfargotunnel.com, proxied.

### Step 5 — Pull secret in new namespace

```
# App secrets (env vars the pod reads via envFrom)
kubectl create secret generic techie-secrets `
  --from-literal=GOOGLE_API_KEY="" `
  --from-literal=TWILIO_ACCOUNT_SID="" `
  --from-literal=TWILIO_AUTH_TOKEN="" `
  --from-literal=TWILIO_PHONE_NUMBER="" `
  --from-literal=API_KEY="pick_a_long_random_string" `
  -n techie


# GHCR pull secret (rotate the PAT first!)
$PAT = "ghp_YOUR_NEW_PAT"
kubectl create secret docker-registry ghcr-secret `
  --docker-server=ghcr.io `
  --docker-username=adriensieg `
  --docker-password=$PAT `
  --docker-email=adriensieg@hotmail.fr `
  -n techie
```

We can get your GitHub Personal Access Token (PAT) https://github.com/settings/tokens

```
kubectl create secret docker-registry ghcr-secret --docker-server=ghcr.io --docker-username=adriensieg --docker-password=$PAT --docker-email=adriensieg@hotmail.fr -n techie
```

Build into an ARM64 Docker image

```
cd C:\Users\cloti\Desktop\HandsOn\onpremise-private-k3-cluster-raspberry

docker buildx build --platform linux/arm64 -t ghcr.io/adriensieg/techie-twillio-gtw:latest --push spaces/techie/apps/twillio-gtw
```

Then link it: `https://github.com/users/adriensieg/packages/container/techie-twillio-gtw/settings`

→ Manage Actions access → add repo with Write. Skips the 403 on first Actions build.

### Register ArgoCD app + push

```
kubectl apply -f argocd/apps/private.yaml

git pull
git add .
git commit -m "feat: add private workspace with adrien app"
git push
```