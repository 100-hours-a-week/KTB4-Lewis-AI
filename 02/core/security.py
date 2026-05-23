from fastapi import Header, HTTPException


def get_anonymous_id(x_anonymous_id: str = Header(...)) -> str:
    """
    클라이언트가 전송한 X-Anonymous-ID 헤더에서 익명 식별자를 추출합니다.
    헤더가 없거나 빈 값이면 400 에러를 반환합니다.
    """
    if not x_anonymous_id or not x_anonymous_id.strip():
        raise HTTPException(
            status_code=400,
            detail="X-Anonymous-ID 헤더가 필요합니다. 고유한 UUID를 전달해주세요.",
        )
    return x_anonymous_id.strip()
