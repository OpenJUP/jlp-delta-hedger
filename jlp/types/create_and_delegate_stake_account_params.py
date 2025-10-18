from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class CreateAndDelegateStakeAccountParamsJSON(typing.TypedDict):
    stake_account_index: int
    stake_amount_lamports: int


@dataclass
class CreateAndDelegateStakeAccountParams:
    layout: typing.ClassVar = borsh.CStruct(
        "stake_account_index" / borsh.U64, "stake_amount_lamports" / borsh.U64
    )
    stake_account_index: int
    stake_amount_lamports: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "CreateAndDelegateStakeAccountParams":
        return cls(
            stake_account_index=obj.stake_account_index,
            stake_amount_lamports=obj.stake_amount_lamports,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "stake_account_index": self.stake_account_index,
            "stake_amount_lamports": self.stake_amount_lamports,
        }

    def to_json(self) -> CreateAndDelegateStakeAccountParamsJSON:
        return {
            "stake_account_index": self.stake_account_index,
            "stake_amount_lamports": self.stake_amount_lamports,
        }

    @classmethod
    def from_json(
        cls, obj: CreateAndDelegateStakeAccountParamsJSON
    ) -> "CreateAndDelegateStakeAccountParams":
        return cls(
            stake_account_index=obj["stake_account_index"],
            stake_amount_lamports=obj["stake_amount_lamports"],
        )
