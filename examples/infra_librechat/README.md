# Self-Healing K8s Agent with LibreChat + MCP

Demo that spins up LibreChat UI, a K8s MCP server, and a broken NGINX deployment (typo'd image), then lets you fix it via chat.

Prerequisites:
- [kubectl](https://kubernetes.io/docs/reference/kubectl/)
- [kind](https://kind.sigs.k8s.io/)
- [uv](https://github.com/astral-sh/uv)
- OPENAI_API_KEY or equivalent

Quickstart:

```bash
make setup  
export OPENAI_API_KEY=…  
make create-all  
make open-librechat  
```


Example:

![Self-healing agent fixing typo](docs/3.png)


Cleanup:

```bash
make clean-all
```
