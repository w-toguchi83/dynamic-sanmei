"""カーソルベースページネーション用のエンコード・デコードユーティリティ.

created_atとentity_idの複合カーソルをbase64エンコードし、
ページネーションのカーソルトークンとして使用する。

カーソル形式: base64(created_at_iso:entity_uuid)
"""

from __future__ import annotations

import base64
from datetime import datetime
from uuid import UUID


class CursorValidationError(Exception):
    """カーソル文字列の検証エラー.

    エンコード時またはデコード時にカーソルが無効な場合に発生する。
    """

    def __init__(self, message: str) -> None:
        """Initialize CursorValidationError."""
        self.message = message
        super().__init__(message)


def encode_cursor(created_at: datetime, entity_id: UUID) -> str:
    """created_atとentity_idから複合カーソル文字列を生成する.

    Args:
        created_at: エンティティの作成日時（タイムゾーン情報必須）
        entity_id: エンティティのUUID

    Returns:
        base64urlエンコードされたカーソル文字列

    Raises:
        CursorValidationError: created_atがtimezone-naiveな場合
    """
    if created_at.tzinfo is None:
        raise CursorValidationError("created_at must be timezone-aware")

    payload = f"{created_at.isoformat()}:{entity_id}"
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    """カーソル文字列をcreated_atとentity_idにデコードする.

    UUIDは常に36文字（ハイフン付き標準形式）のため、
    ペイロード末尾36文字をUUID部分として分離する。
    ISO形式の日時文字列にもコロンが含まれるため、
    単純な文字列分割ではなく末尾固定長で分離する。

    Args:
        cursor: base64urlエンコードされたカーソル文字列

    Returns:
        (created_at, entity_id) のタプル

    Raises:
        CursorValidationError: カーソルが不正な場合
    """
    try:
        decoded_bytes = base64.urlsafe_b64decode(cursor)
        payload = decoded_bytes.decode()
    except Exception as err:
        raise CursorValidationError("Invalid cursor: failed to decode base64") from err

    # UUID部分は末尾36文字（例: "550e8400-e29b-41d4-a716-446655440000"）
    # セパレータのコロン1文字を含めて最低37文字必要
    uuid_length = 36
    min_length = uuid_length + 1  # コロン + UUID

    if len(payload) < min_length:
        raise CursorValidationError("Invalid cursor: payload too short")

    uuid_str = payload[-uuid_length:]
    # セパレータがコロンであることを確認
    separator_index = len(payload) - uuid_length - 1

    if payload[separator_index] != ":":
        raise CursorValidationError("Invalid cursor: missing separator")

    iso_str = payload[:separator_index]

    try:
        entity_id = UUID(uuid_str)
    except ValueError as err:
        raise CursorValidationError("Invalid cursor: invalid UUID") from err

    try:
        created_at = datetime.fromisoformat(iso_str)
    except ValueError as err:
        raise CursorValidationError("Invalid cursor: invalid datetime") from err

    return created_at, entity_id
