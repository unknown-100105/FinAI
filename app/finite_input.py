"""Shared request base that rejects NaN and infinite numeric values."""
from __future__ import annotations

import pydantic
from pydantic import BaseModel


if int(pydantic.__version__.split(".", 1)[0]) >= 2:
    from pydantic import ConfigDict

    class FiniteInputModel(BaseModel):
        model_config: ConfigDict = ConfigDict(allow_inf_nan=False)
else:
    class FiniteInputModel(BaseModel):
        class Config:
            allow_inf_nan = False
