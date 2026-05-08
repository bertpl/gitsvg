"""Shared pydantic configuration for all operation models."""

from pydantic import BaseModel, ConfigDict


class OpBase(BaseModel):
    """Base class for all operation models.

    Provides the shared pydantic configuration: unknown fields are
    rejected (`extra="forbid"`) so agents get clear errors on typos
    rather than silent acceptance.
    """

    model_config = ConfigDict(extra="forbid")
