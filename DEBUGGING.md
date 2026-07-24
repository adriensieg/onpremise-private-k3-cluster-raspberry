# Debugging Guide — When Your App Isn't Working

A repeatable path from **"the page is broken"** to **"I know exactly which layer failed."**

---

# The Mental Model

Your request passes through **five layers**.

Test each in order — **the first failure is your answer**.

```text
Browser
    │
    ▼
Cloudflare
    │
    ▼
NGINX Ingress
    │
    ▼
Service
    │
    ▼
Pod (your code)
```

Deployment follows a completely separate path:

```text
git push
    │
    ▼
GitHub Actions
    │
    ▼
GHCR
    │
    ▼
ArgoCD
    │
    ▼
Pod
```

> **Most confusion comes from mixing these up.**
>
> - A browser **404** is usually a **routing problem**.
> - A pod running **old code** is a **deployment pipeline problem**.
>
> Diagnose them separately.

---

# Step 1 — Is the Backend Actually Working?

Bypass the browser entirely.

```powershell
curl.exe https://devailab.work/helloapi/api/hello
```

### If it returns JSON

✅ Backend, Service, Ingress, and Cloudflare Tunnel are all working.

Your problem is in the frontend or browser.

➡ Continue to **Step 5**.

### If it returns a 404 HTML page from nginx

This is a routing problem.

➡ Continue to **Step 2**.

### If it times out or connection is refused

Tunnel or ingress is probably down.

```powershell
kubectl get pods -n cloudflare
kubectl get pods -n ingress-nginx
```

---

# Step 2 — Is the Pod Running?

```powershell
kubectl get pods -n public
```

| Status | Meaning | Next Command |
|---------|---------|--------------|
| Running 1/1 | Healthy | Continue to Step 3 |
| ImagePullBackOff | Cannot pull image from GHCR | `kubectl describe pod -n public <pod-name>` |
| CrashLoopBackOff | App crashes on startup | `kubectl logs -n public <pod-name> --previous` |
| Pending | No node capacity | `kubectl describe pod -n public <pod-name>` |
| 0/1 Running | Readiness probe failing | `kubectl logs -n public <pod-name>` |

To get the complete picture:

```powershell
kubectl describe pod -n public -l app=helloapi
```

Read the **Events:** section at the bottom.

Kubernetes tells you exactly what it tried and why it failed.

---

# Step 3 — Read Your Application Logs

View recent logs:

```powershell
kubectl logs -n public -l app=helloapi --tail=100
```

Follow logs live:

```powershell
kubectl logs -n public -l app=helloapi -f
```

If the pod restarted:

```powershell
kubectl logs -n public -l app=helloapi --previous
```

---

# Step 4 — Is Routing Configured Correctly?

Check ingress:

```powershell
kubectl get ingress -n public

kubectl describe ingress public-ingress -n public
```

Check service endpoints:

```powershell
kubectl get endpoints -n public
```

An empty **ENDPOINTS** column means the Service selector matches no Pods.

View NGINX logs:

```powershell
kubectl logs -n ingress-nginx \
-l app.kubernetes.io/name=ingress-nginx \
--tail=50
```

Bypass ingress completely:

```powershell
kubectl port-forward -n public svc/helloapi 9000:8000
```

In another terminal:

```powershell
curl.exe http://localhost:9000/api/hello
```

If it works through port-forward but not through ingress:

✅ The problem is your ingress path or rewrite rule.

---

# Step 5 — Browser-Side Issues

Open **Developer Tools**

- Console
- Network

Read the **actual request URL**, not the one you think you're calling.

| Error | Cause | Fix |
|-------|-------|-----|
| `Unexpected token '<'` | HTML returned instead of JSON (usually a 404 page) | Verify the request URL |
| 404 on a path missing your app prefix | Relative URL resolved against `/` | Use `fetch('/helloapi/api/hello')` |
| Old behavior after deployment | Browser cache | Hard refresh (`Ctrl + Shift + R`) or use a private window |

## The Relative Path Trap

A page served at:

```
/helloapi
```

without a trailing slash will resolve

```javascript
fetch("api/hello")
```

to

```
/api/hello
```

instead of

```
/helloapi/api/hello
```

**Always use absolute paths** for applications hosted under a URL prefix.

---

# Step 6 — Is Your Code Actually Deployed?

Most **"my fix didn't work"** problems happen here.

---

## 1. Does the Pod Run a SHA-Tagged Image?

```powershell
kubectl get pod -n public -l app=helloapi \
-o jsonpath="{.items[0].spec.containers[0].image}"
```

### If you see

```
:latest
```

GitHub Actions never built your code.

➡ Continue to **Step 7**

### If you see

```
:abc123...
```

CI succeeded.

Compare that SHA with your latest Git commit.

---

## 2. Is ArgoCD on Your Latest Commit?

```powershell
kubectl get application public -n argocd \
-o jsonpath="{.status.sync.revision}"

git log --oneline -1
```

The SHAs should match.

If they don't:

```powershell
kubectl patch application public \
-n argocd \
--type merge \
-p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
```

---

## 3. Is ArgoCD Healthy?

```powershell
kubectl get application public -n argocd -o wide

kubectl get pods -n argocd
```

`argocd-repo-server` must be:

```
1/1 Running
```

If ArgoCD reports **Synced** and **Healthy** but your namespace is empty, verify your Application contains:

```yaml
directory:
  recurse: true
```

---

# Step 7 — Debugging GitHub Actions

Open:

https://github.com/adriensieg/onpremise-private-k3-cluster-raspberry/actions

---

## No Workflow Runs

Your trigger probably didn't match.

Inspect the committed workflow:

```powershell
git show HEAD:.github/workflows/deploy.yaml |
Select-Object -First 12
```

Check:

- `branches: [master]`
- `paths:`

Then inspect your latest commit:

```powershell
git show --stat HEAD
```

### Empty Commits Never Trigger Path Filters

This won't trigger builds:

```powershell
git commit --allow-empty
```

Instead make a real change:

```powershell
Add-Content spaces\public\apps\helloapi\app\main.py "`n# trigger"

git add .

git commit -m "ci: trigger build"

git push
```

---

## A Workflow Exists

Read the **Annotations** section first.

Common messages:

| Annotation | Meaning | Fix |
|------------|---------|-----|
| `Invalid format ' {'` | Multi-line JSON written to `$GITHUB_OUTPUT` | Use `jq -c` |
| `Unable to process file command 'output'` | Same issue | Use `jq -c` |
| `Node.js 20 is deprecated` | Warning only | Ignore |

Remember:

> `$GITHUB_OUTPUT` only accepts **single-line `key=value` pairs**.
>
> Pretty-printed JSON is the most common cause of workflow failures.

---

## build-and-push Was Skipped

The build matrix was empty.

Inspect the **Build changed-app matrix** step.

Add a debug output:

```yaml
echo "Detected: $MATRIX"
```

Usually your changed files didn't match the expected path or pattern.

---

## build-and-push Failed

Most common causes:

- `buildx` timeout (ARM64 emulation is slow)
- Git push denied (`contents: write`)
- GHCR push denied (`packages: write`)

---

# Emergency Bypass — Deploy Without CI

When you need a fix immediately:

```powershell
$PAT = "ghp_YOUR_TOKEN"

echo $PAT |
docker login ghcr.io \
-u adriensieg \
--password-stdin

docker buildx build `
--platform linux/arm64 `
-t ghcr.io/adriensieg/public-helloapi:latest `
--push spaces/public/apps/helloapi

kubectl rollout restart deployment helloapi -n public

kubectl rollout status deployment helloapi -n public
```

This proves whether your code is correct while completely bypassing the CI pipeline.

---

# Quick Reference

## Cluster Health

```powershell
kubectl get pods -n public

kubectl get application public -n argocd -o wide
```

---

## What's Actually Deployed?

```powershell
kubectl get pod -n public -l app=helloapi \
-o jsonpath="{.items[0].spec.containers[0].image}"

kubectl get application public -n argocd \
-o jsonpath="{.status.sync.revision}"

git log --oneline -1
```

---

## Logs

```powershell
kubectl logs -n public -l app=helloapi --tail=100

kubectl logs -n public -l app=helloapi -f

kubectl logs -n public -l app=helloapi --previous

kubectl logs -n ingress-nginx \
-l app.kubernetes.io/name=ingress-nginx \
--tail=50
```

---

## Why Is This Pod Unhappy?

```powershell
kubectl describe pod -n public -l app=helloapi
```

---

## Test Each Layer

```powershell
# Full request path
curl.exe https://devailab.work/helloapi/api/hello

# Skip ingress entirely
kubectl port-forward -n public svc/helloapi 9000:8000
```

---

## Force ArgoCD to Refresh

```powershell
kubectl patch application public \
-n argocd \
--type merge \
-p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
```

---

# The Three Lessons From This Session

## 1. `:latest` Means CI Never Ran

A SHA-tagged image proves the entire deployment pipeline succeeded.

This single check immediately tells you whether to debug:

- your application
- or your deployment pipeline

---

## 2. Empty Commits Don't Trigger Path Filters

If you're forcing a build, modify a real file under:

- `app/`
- `Dockerfile`

---

## 3. Read the Annotations Before the Logs

Workflow syntax problems almost always appear in the **Annotations** panel before they're obvious in the logs.

It is the fastest place to diagnose a failed GitHub Actions workflow.