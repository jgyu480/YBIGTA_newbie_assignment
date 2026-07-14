from __future__ import annotations

from typing import Optional


def build_request(host: str, path: str) -> bytes:
    """
    HTTP/1.1 형식의 GET 요청 메시지를 바이트 형태로 생성합니다.

    요청 대상 경로가 슬래시(/)로 시작하지 않으면 앞에 슬래시를 추가한
    뒤, HTTP 요청 라인과 필수 헤더를 구성합니다.

    생성되는 요청에는 다음 내용이 포함됩니다.

    - 요청 라인:
      GET {path} HTTP/1.1
    - Host 헤더:
      요청 대상 도메인을 서버에 전달합니다.
    - Connection: close 헤더:
      서버가 응답을 모두 전송한 뒤 TCP 연결을 종료하도록 요청합니다.

    HTTP 규격에 따라 모든 줄은 CRLF("\\r\\n")로 끝나며, 헤더의
    끝을 표시하기 위해 마지막에 빈 줄이 추가됩니다. 완성된 문자열은
    UTF-8로 인코딩하여 bytes 객체로 반환합니다.

    Args:
        host: HTTP 요청을 보낼 대상 도메인입니다.
            예: "example.com"
        path: 요청할 리소스의 경로입니다.
            예: "/", "/index.html", "search?q=test"

    Returns:
        HTTP/1.1 GET 요청 메시지를 담은 bytes 객체를 반환합니다.

    Examples:
        >>> build_request("example.com", "/")
        b'GET / HTTP/1.1\\r\\nHost: example.com\\r\\nConnection: close\\r\\n\\r\\n'
    """
    if not path.startswith("/"):
        path = "/" + path

    ###########################################################
    # HTTP/1.1 규격에 맞게 요청 문자열을 구성합니다.
    # 각 줄의 끝에는 \r\n을 사용하고, 헤더의 끝에는 빈 줄을
    # 나타내는 \r\n을 한 번 더 추가합니다.

    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )

    ###########################################################

    return req.encode("utf-8")


def send_and_recv(sock, request: bytes, max_bytes: int) -> bytes:
    """
    연결된 TCP 소켓으로 HTTP 요청을 보내고 서버 응답을 수신합니다.

    요청 전체를 sendall()로 전송한 뒤, 서버가 연결을 종료하거나 더 이상
    데이터를 보내지 않을 때까지 최대 4096바이트씩 반복하여 수신합니다.
    수신한 전체 데이터 크기가 max_bytes를 초과하면 반복을 중단합니다.

    Args:
        sock: TCP 연결이 완료된 소켓 객체입니다.
        request: 서버에 전송할 HTTP 요청 메시지입니다.
        max_bytes: 수신할 응답 데이터의 최대 크기 기준입니다.

    Returns:
        여러 번 나누어 수신한 응답 데이터를 하나로 합친 bytes 객체를
        반환합니다.
    """
    sock.sendall(request)

    chunks: list[bytes] = []
    total = 0

    while True:
        data = sock.recv(4096)

        if not data:
            break

        chunks.append(data)
        total += len(data)

        if total > max_bytes:
            break

    return b"".join(chunks)


def parse_status_and_preview(
    raw: bytes,
    max_preview: int = 200,
) -> tuple[Optional[int], str, Optional[str]]:
    """
    HTTP 원시 응답에서 상태 코드와 본문 미리보기를 추출합니다.

    HTTP 응답은 헤더와 본문 사이에 존재하는 CRLF 두 번,
    즉 b"\\r\\n\\r\\n"을 기준으로 구분합니다. 헤더의 첫 번째 줄인
    Status Line을 분석하여 정수 형태의 상태 코드를 추출하고, 본문의
    앞부분을 max_preview 바이트만큼 잘라 문자열로 변환합니다.

    정상적인 Status Line은 일반적으로 다음 형태입니다.

        HTTP/1.1 200 OK

    이를 공백 기준으로 분리하면 두 번째 항목인 "200"이 상태 코드가
    됩니다.

    응답 형식이 올바르지 않은 경우에는 예외를 외부로 전달하지 않고,
    상태 코드와 미리보기 대신 오류 메시지를 반환합니다. 본문에 UTF-8로
    표현할 수 없는 바이트가 포함된 경우에는 해당 부분을 대체 문자로
    변환하여 파싱을 계속합니다.

    Args:
        raw: 서버로부터 수신한 전체 HTTP 응답 데이터입니다.
        max_preview: 본문에서 미리보기로 변환할 최대 바이트 수입니다.
            기본값은 200입니다.

    Returns:
        다음 세 값을 원소로 가지는 튜플을 반환합니다.

        성공한 경우:
            - Optional[int]: HTTP 상태 코드
            - str: 응답 본문의 앞부분
            - Optional[str]: None

        실패한 경우:
            - Optional[int]: None
            - str: 빈 문자열
            - Optional[str]: 응답이 올바르지 않은 이유를 설명하는
              오류 메시지

    Examples:
        >>> raw = (
        ...     b"HTTP/1.1 200 OK\\r\\n"
        ...     b"Content-Type: text/plain\\r\\n"
        ...     b"\\r\\n"
        ...     b"HELLO_WORLD"
        ... )
        >>> parse_status_and_preview(raw, max_preview=5)
        (200, 'HELLO', None)
    """

    ###########################################################
    # HTTP 응답 파싱
    # 1. b"\r\n\r\n"을 기준으로 헤더와 본문을 구분합니다.
    # 2. 헤더 첫 줄에서 HTTP 상태 코드를 추출합니다.
    # 3. 본문 앞부분을 max_preview 바이트만큼 문자열로 변환합니다.

    separator = b"\r\n\r\n"
    boundary = raw.find(separator)

    if boundary == -1:
        return (
            None,
            "",
            "Invalid HTTP response: header/body separator not found",
        )

    header_bytes = raw[:boundary]
    body = raw[boundary + len(separator):]

    try:
        # HTTP 헤더는 임의의 바이트 값을 손실 없이 문자로 대응시키기
        # 위해 ISO-8859-1로 디코딩합니다.
        header = header_bytes.decode("iso-8859-1")

        status_line = header.split("\r\n", 1)[0]
        status_parts = status_line.split()

        if len(status_parts) < 2:
            return (
                None,
                "",
                "Invalid HTTP response: malformed status line",
            )

        if not status_parts[0].startswith("HTTP/"):
            return (
                None,
                "",
                "Invalid HTTP response: invalid HTTP version",
            )

        status_code = int(status_parts[1])

        preview = body[:max_preview].decode(
            "utf-8",
            errors="replace",
        )

        error = None

    except Exception as e:
        status_code = None
        preview = ""
        error = f"Invalid HTTP response: {e}"

    ###########################################################

    return status_code, preview, error