from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class SwapWithTokenLedgerParamsJSON(typing.TypedDict):
    min_amount_out: int


@dataclass
class SwapWithTokenLedgerParams:
    layout: typing.ClassVar = borsh.CStruct("min_amount_out" / borsh.U64)
    min_amount_out: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "SwapWithTokenLedgerParams":
        return cls(min_amount_out=obj.min_amount_out)

    def to_encodable(self) -> dict[str, typing.Any]:
        return {"min_amount_out": self.min_amount_out}

    def to_json(self) -> SwapWithTokenLedgerParamsJSON:
        return {"min_amount_out": self.min_amount_out}

    @classmethod
    def from_json(
        cls, obj: SwapWithTokenLedgerParamsJSON
    ) -> "SwapWithTokenLedgerParams":
        return cls(min_amount_out=obj["min_amount_out"])
