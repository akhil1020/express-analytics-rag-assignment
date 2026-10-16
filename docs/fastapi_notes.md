# FastAPI request handling

FastAPI reads request data from Python type annotations. A Pydantic model declared as a path-operation argument validates JSON request bodies and returns a 422 response when the request data does not meet model constraints.

For file uploads, use `UploadFile`. It provides the filename, declared content type, and an async file interface. A production service should validate file size and should not rely only on the client-supplied MIME type.

Use `HTTPException` to return meaningful client errors. Common choices are 409 for a request that conflicts with application state, 413 for an oversized upload, 415 for an unsupported media type, and 422 for validly formed requests that fail validation.

Source: https://fastapi.tiangolo.com/tutorial/body/ and https://fastapi.tiangolo.com/tutorial/request-files/
