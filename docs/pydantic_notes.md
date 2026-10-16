# Pydantic models and validation

Pydantic models describe structured data using typed fields. Field constraints such as minimum length, maximum length, and default values make an API contract explicit. FastAPI uses those models to validate request bodies and document the API schema.

A model can be serialized with `model_dump()`. This is useful when a validated request needs to be written to persistence because it produces standard Python data rather than a model instance.

Validation belongs at the boundary of an application. Once request data has passed a Pydantic model, workflow code can focus on behavior instead of repeatedly checking basic shapes and types.

Source: https://docs.pydantic.dev/latest/concepts/models/
