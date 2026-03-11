# OAG Demo Application

A sample header-based application for demonstrating Okta Access Gateway authentication.

## Overview

This demo application displays HTTP headers injected by Okta Access Gateway, making it easy to test and demonstrate header-based single sign-on.

**Features:**
- Displays authenticated user information from headers
- Shows all OAG-injected headers
- Provides API endpoints for testing
- Health check endpoint for load balancing

## Quick Start

### Run Locally

```bash
cd app
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:8080` to see the application.

### Run with Docker

```bash
cd app
docker build -t oag-demo-app .
docker run -p 8080:8080 oag-demo-app
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Main page displaying all headers |
| `/health` | Health check endpoint |
| `/api/headers` | JSON response with all headers |
| `/api/user` | JSON response with authenticated user info |

## Deploying to AWS

### Prerequisites

1. OAG infrastructure deployed (see `environments/myorg/oag-infrastructure/`)
2. AWS CLI configured
3. Docker installed

### Deploy Demo App

```bash
# Build and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker build -t oag-demo-app app/
docker tag oag-demo-app:latest <account>.dkr.ecr.<region>.amazonaws.com/oag-demo-app:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/oag-demo-app:latest

# Deploy with Terraform
cd terraform
terraform init
terraform apply
```

## Configuring in OAG

### 1. Create the Application

Use the OAG management script:

```bash
python scripts/manage_oag_apps.py \
  --config examples/oag-demo-app/config/oag_app_config.json \
  --action deploy
```

### 2. Manual Configuration

Or configure manually in OAG Admin Console:

1. Go to **Applications** → **Add**
2. Select **Header Based** → **Create**
3. Configure:
   - **Label**: OAG Demo App
   - **Public Domain**: demo.example.com
   - **Protected Web Resource**: https://your-backend:8080
4. Add attributes:
   - `IDP.login` → Header: `X-Remote-User`
   - `IDP.email` → Header: `X-Remote-Email`
   - `IDP.firstName` → Header: `X-Remote-FirstName`
   - `IDP.lastName` → Header: `X-Remote-LastName`

### 3. Assign Users

Assign users or groups to the application in Okta.

## Testing

### With OAG

1. Navigate to your OAG public URL (e.g., `https://demo.example.com`)
2. Authenticate with Okta
3. View the injected headers displayed by the app

### Without OAG (Simulated Headers)

```bash
curl -H "X-Remote-User: testuser@example.com" \
     -H "X-Remote-Email: testuser@example.com" \
     -H "X-Remote-FirstName: Test" \
     -H "X-Remote-LastName: User" \
     http://localhost:8080/api/user
```

## Configuration

### OAG Application Config

See `config/oag_app_config.json` for the application configuration:

```json
{
  "label": "OAG Demo App",
  "public_domain": "demo.example.com",
  "protected_resources": [
    {
      "url": "https://backend-server:8080",
      "weight": 100
    }
  ],
  "attributes": [
    {
      "source": "IDP",
      "field": "login",
      "type": "Header",
      "name": "X-Remote-User"
    }
  ]
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Application port | 8080 |
| `DEBUG` | Enable debug mode | false |

## Troubleshooting

### No Headers Displayed

1. Verify OAG is properly configured
2. Check that attributes are defined in OAG app
3. Verify user is assigned to the application
4. Check OAG logs for errors

### Health Check Failing

1. Ensure application is running on correct port
2. Check security group allows traffic from ALB
3. Verify `/health` endpoint returns 200

### Certificate Issues

1. Ensure ACM certificate is validated
2. Check ALB listener is using correct certificate
3. Verify DNS points to ALB

## Files

```
oag-demo-app/
├── app/
│   ├── app.py              # Flask application
│   ├── Dockerfile          # Container definition
│   └── requirements.txt    # Python dependencies
├── config/
│   └── oag_app_config.json # OAG application configuration
├── terraform/
│   └── (infrastructure)    # AWS deployment
└── README.md               # This file
```

## Related Documentation

- [OAG Deployment Guide](../../docs/OAG_DEPLOYMENT.md)
- [OAG API Management](../../docs/OAG_API_MANAGEMENT.md)
- [Header Application Best Practices](https://help.okta.com/oag/en-us/content/topics/access-gateway/best-practices-header.htm)
