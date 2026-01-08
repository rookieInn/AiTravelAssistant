from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Union


_DIGITS = "零壹贰叁肆伍陆柒捌玖"
_UNITS_IN_GROUP = ["", "拾", "佰", "仟"]
_GROUP_UNITS = ["", "万", "亿", "兆"]


def _to_decimal_amount(amount: Union[str, int, float, Decimal], *, scale: int = 2) -> Decimal:
    """
    Convert amount to Decimal and quantize to currency scale.

    Note:
    - Never use float internally for finance; if float is passed we still convert,
      but callers should prefer str/int/Decimal to avoid binary rounding noise.
    """
    d = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    q = Decimal("1").scaleb(-scale)  # 0.01 when scale=2
    return d.quantize(q, rounding=ROUND_HALF_UP)


def _four_digits_to_upper(n: int) -> str:
    """
    Convert 0..9999 to RMB uppercase without group unit.
    """
    assert 0 <= n <= 9999
    if n == 0:
        return ""

    parts: list[str] = []
    zero_pending = False
    for idx in range(3, -1, -1):
        div = 10**idx
        digit = (n // div) % 10
        if digit == 0:
            zero_pending = True if parts else zero_pending
            continue
        if zero_pending:
            parts.append(_DIGITS[0])
            zero_pending = False
        parts.append(_DIGITS[digit] + _UNITS_IN_GROUP[idx])
    return "".join(parts)


def rmb_upper(amount: Union[str, int, float, Decimal], *, voided: bool = False) -> str:
    """
    Convert numeric amount to Chinese RMB uppercase format.

    Examples:
    - 0 -> 零元整
    - 1234.56 -> 壹仟贰佰叁拾肆元伍角陆分
    - -10 -> 负壹拾元整

    Args:
        amount: numeric amount; rounded to 2 decimals (四舍五入到分).
        voided: if True, returns "作废" (common voucher/invoice mark).
    """
    if voided:
        return "作废"

    d = _to_decimal_amount(amount, scale=2)
    if d == 0:
        return "零元整"

    sign = ""
    if d < 0:
        sign = "负"
        d = -d

    yuan = int(d)  # integer part
    fen_total = int((d * 100) % 100)  # 0..99
    jiao = fen_total // 10
    fen = fen_total % 10

    # Integer part
    int_parts: list[str] = []
    if yuan == 0:
        int_parts.append("零")
    else:
        group_idx = 0
        need_zero = False
        while yuan > 0:
            group = yuan % 10000
            yuan //= 10000
            group_upper = _four_digits_to_upper(group)
            if group == 0:
                need_zero = True if int_parts else need_zero
                group_idx += 1
                continue

            if need_zero and int_parts:
                # Crossing group boundary with skipped zeros needs a single 零
                int_parts.append("零")
                need_zero = False

            if group_upper:
                int_parts.append(group_upper + _GROUP_UNITS[group_idx])
            group_idx += 1

        int_str = "".join(reversed(int_parts))
        # Cleanup repeated 零
        while "零零" in int_str:
            int_str = int_str.replace("零零", "零")
        int_str = int_str.rstrip("零")
        int_parts = [int_str] if int_str else ["零"]

    result = sign + "".join(int_parts) + "元"

    # Fractional part
    if jiao == 0 and fen == 0:
        return result + "整"

    frac_parts: list[str] = []
    if jiao != 0:
        frac_parts.append(_DIGITS[jiao] + "角")
    else:
        # If there is fen but no jiao, we need 零 to bridge (e.g. 1.05 => 壹元零伍分)
        if fen != 0:
            frac_parts.append("零")
    if fen != 0:
        frac_parts.append(_DIGITS[fen] + "分")

    return result + "".join(frac_parts)

