#!/usr/bin/env python3

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="DRMS Configuration Generator", version="1.0.0")

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"
templates = Jinja2Templates(directory=str(templates_dir))

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Configuration templates
IDE_CONFIGS = {
    "cursor": {
        "name": "Cursor Configuration",
        "description": "Configuration for Cursor AI IDE",
        "template": {
            "mcpServers": {
                "drms": {
                    "command": "drms",
                    "args": ["start"],
                    "env": {
                        "DRMS_LOG_LEVEL": "INFO"
                    }
                }
            }
        }
    },
    "vscode": {
        "name": "VS Code Configuration", 
        "description": "Configuration for Visual Studio Code",
        "template": {
            "name": "drms",
            "command": "drms",
            "args": ["start"],
            "transport": "stdio"
        }
    },
    "windsurf": {
        "name": "Windsurf Configuration",
        "description": "Configuration for Windsurf IDE",
        "template": {
            "mcpServers": {
                "drms": {
                    "command": "drms",
                    "args": ["start"],
                    "transport": "stdio"
                }
            }
        }
    },
    "claude-dev": {
        "name": "Claude Dev Configuration",
        "description": "Configuration for Claude Dev extension",
        "template": {
            "name": "DRMS",
            "serverPath": "drms",
            "args": ["start"],
            "description": "Documentation RAG MCP Server"
        }
    }
}

DEPLOYMENT_CONFIGS = {
    "docker": {
        "name": "Docker Compose",
        "description": "Docker deployment configuration",
        "files": {
            "docker-compose.yml": """version: '3.8'
services:
  drms-server:
    image: drms/server:latest
    ports:
      - "{port}:8000"
    environment:
      - DRMS_API_HOST=0.0.0.0
      - DRMS_API_PORT=8000
      - DRMS_LOG_LEVEL={log_level}
      - OPENAI_API_KEY={openai_key}
    volumes:
      - drms_data:/app/data
    restart: unless-stopped

volumes:
  drms_data:
    driver: local
"""
        }
    },
    "kubernetes": {
        "name": "Kubernetes",
        "description": "Kubernetes deployment configuration",
        "files": {
            "deployment.yml": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: drms-server
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: drms-server
  template:
    metadata:
      labels:
        app: drms-server
    spec:
      containers:
      - name: drms-server
        image: drms/server:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: drms-secrets
              key: openai-api-key
        - name: DRMS_LOG_LEVEL
          value: "{log_level}"
---
apiVersion: v1
kind: Service
metadata:
  name: drms-service
spec:
  selector:
    app: drms-server
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
"""
        }
    }
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ide", response_class=HTMLResponse)
async def ide_config(request: Request):
    return templates.TemplateResponse("ide_config.html", {
        "request": request,
        "ide_configs": IDE_CONFIGS
    })

@app.get("/deployment", response_class=HTMLResponse)
async def deployment_config(request: Request):
    return templates.TemplateResponse("deployment_config.html", {
        "request": request,
        "deployment_configs": DEPLOYMENT_CONFIGS
    })

@app.post("/generate/ide")
async def generate_ide_config(
    ide: str = Form(...),
    host: str = Form("localhost"),
    port: int = Form(8000),
    log_level: str = Form("INFO"),
    custom_args: str = Form("")
):
    if ide not in IDE_CONFIGS:
        raise HTTPException(status_code=400, detail="Invalid IDE selection")
    
    config = IDE_CONFIGS[ide]["template"].copy()
    
    # Customize configuration based on form inputs
    if ide in ["cursor", "windsurf"]:
        if "drms" in config.get("mcpServers", {}):
            if "env" not in config["mcpServers"]["drms"]:
                config["mcpServers"]["drms"]["env"] = {}
            config["mcpServers"]["drms"]["env"]["DRMS_HOST"] = host
            config["mcpServers"]["drms"]["env"]["DRMS_PORT"] = str(port)
            config["mcpServers"]["drms"]["env"]["DRMS_LOG_LEVEL"] = log_level
            
            if custom_args:
                config["mcpServers"]["drms"]["args"].extend(custom_args.split())
    
    elif ide == "vscode":
        config["host"] = host
        config["port"] = port
        if custom_args:
            config["args"].extend(custom_args.split())
    
    elif ide == "claude-dev":
        if custom_args:
            config["args"].extend(custom_args.split())
    
    return JSONResponse({
        "config": config,
        "filename": f"{ide}_drms_config.json"
    })

@app.post("/generate/deployment")
async def generate_deployment_config(
    deployment_type: str = Form(...),
    port: int = Form(8000),
    replicas: int = Form(2),
    log_level: str = Form("INFO"),
    openai_key: str = Form("")
):
    if deployment_type not in DEPLOYMENT_CONFIGS:
        raise HTTPException(status_code=400, detail="Invalid deployment type")
    
    config_info = DEPLOYMENT_CONFIGS[deployment_type]
    files = {}
    
    for filename, template in config_info["files"].items():
        files[filename] = template.format(
            port=port,
            replicas=replicas,
            log_level=log_level,
            openai_key=openai_key or "${OPENAI_API_KEY}"
        )
    
    return JSONResponse({
        "files": files,
        "deployment_type": deployment_type
    })

@app.get("/api/ide-configs")
async def get_ide_configs():
    return JSONResponse(IDE_CONFIGS)

@app.get("/api/deployment-configs")
async def get_deployment_configs():
    return JSONResponse(DEPLOYMENT_CONFIGS)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Create template directories if they don't exist
    templates_dir.mkdir(exist_ok=True)
    static_dir.mkdir(exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8080)