---
name: "api-design"
description: "API Design Assistant with flexible options"
arguments:
  - name: "endpoint"
    description: "API endpoint path"
    required: true
  - name: "method"
    description: "HTTP method"
    default: "GET"
  - name: "auth"
    description: "Authentication type"
    default: "Bearer"
  - name: "description"
    description: "Endpoint description"
    required: true
---

Design an API endpoint for: {endpoint}

Method: {method}
Authentication: {auth}
Purpose: {description}

Provide:
1. Detailed endpoint specification
2. Request/response examples
3. Error handling
4. Security considerations
