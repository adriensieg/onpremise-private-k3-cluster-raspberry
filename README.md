# onpremise-private-k3-cluster-raspberry
Building a bare-metal Kubernetes cluster on Raspberry Pi computers

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