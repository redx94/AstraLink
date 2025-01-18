# AstraLink API Reference

This document lists all application EST points, arguments to call, structured data, and responses.

## Featured Endpoints

- /provision-esim
  - Description: Provides an eSIM using based on details.
  - Parameters: {user_id, metadata}
  - Response: {"status": active}

- /status/eSIM
  - Description: Gets the current status of an eSIM.
  - Parameters: {user_id}
  - Response: {"data": "current status"}