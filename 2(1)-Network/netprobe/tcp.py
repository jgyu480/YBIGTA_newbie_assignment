from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class TCPConnectResult:
    ip: Optional[str]
    port: int
    connect_ms: Optional[float]
    local_addr: Optional[tuple[str, int]]
    peer_addr: Optional[tuple[str, int]]
    error: Optional[str]
    sock: Optional[socket.socket]


def _make_socket(ip: str, timeout: float) -> socket.socket:
    """
    IP 주소의 버전에 맞는 TCP 소켓을 생성하고 timeout을 설정합니다.

    주소 문자열에 콜론(:)이 포함되어 있으면 IPv6 주소로 판단하여
    AF_INET6 소켓을 생성하고, 그렇지 않으면 IPv4 주소로 판단하여
    AF_INET 소켓을 생성합니다.

    Args:
        ip: 연결할 서버의 IPv4 또는 IPv6 주소입니다.
        timeout: 소켓 연결 및 통신에 적용할 제한 시간입니다.
            단위는 초입니다.

    Returns:
        주소 체계와 timeout이 설정된 TCP 소켓 객체를 반환합니다.
    """
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    s = socket.socket(family, socket.SOCK_STREAM)
    s.settimeout(timeout)
    return s


def connect_one(ip: str, port: int, timeout: float):
    """
    하나의 IP 주소와 포트에 TCP 연결을 시도하고 연결 시간을 측정합니다.

    IP 주소의 버전에 맞는 소켓을 생성한 뒤 socket.connect()를 호출합니다.
    연결 직전과 직후에 time.perf_counter() 값을 측정하여 실제 TCP 연결에
    걸린 시간을 밀리초 단위로 계산합니다.

    연결에 성공하면 열린 소켓과 연결 시간을 반환합니다. 연결 과정에서
    예외가 발생하면 생성한 소켓을 닫고, 소켓과 연결 시간 대신 None과
    오류 메시지를 반환합니다.

    Args:
        ip: 연결할 서버의 IPv4 또는 IPv6 주소입니다.
        port: 연결할 서버의 TCP 포트 번호입니다.
        timeout: 연결 시도에 적용할 제한 시간입니다. 단위는 초입니다.

    Returns:
        다음 세 값을 원소로 가지는 튜플을 반환합니다.

        성공한 경우:
            - socket.socket: 연결이 완료된 소켓 객체
            - float: TCP 연결에 걸린 시간(ms)
            - None: 오류가 없음을 나타냄

        실패한 경우:
            - None: 연결된 소켓이 없음
            - None: 측정된 연결 시간이 없음
            - str: 연결 실패 원인을 나타내는 오류 메시지

    Notes:
        성공한 경우 반환된 소켓은 이 함수에서 닫지 않습니다. 이후 HTTP
        요청에 사용한 뒤 호출한 측에서 닫아야 합니다.
    """
    s: Optional[socket.socket] = None

    try:
        s = _make_socket(ip, timeout)
        start = time.perf_counter()

        ###########################################################
        # 연결 직전과 직후의 시간을 측정하여 연결에 걸린 시간(ms)을
        # 계산합니다. perf_counter()의 단위는 초이므로 1000을 곱합니다.

        s.connect((ip, port))
        ms = (time.perf_counter() - start) * 1000

        ###########################################################

        return s, ms, None
    except Exception as e:
        try:
            if s is not None:
                s.close()
        except Exception:
            pass

        return None, None, str(e)


def connect_with_fallback(
    ips: list[str],
    port: int,
    timeout: float,
    prefer: str = "any",
) -> TCPConnectResult:
    """
    여러 IP 주소에 순차적으로 TCP 연결을 시도합니다.

    하나의 도메인에서 IPv4와 IPv6를 포함한 여러 IP 주소가 조회될 수
    있으므로, prefer 정책에 따라 연결 시도 순서를 정한 뒤 각 주소에
    connect_one()을 호출합니다. 가장 먼저 연결에 성공한 주소의 소켓을
    최종 연결로 사용합니다.

    연결에 성공하면 실제로 연결된 IP 주소, 연결 시간, 로컬 주소,
    서버 주소 및 소켓 객체를 TCPConnectResult에 담아 반환합니다.
    모든 주소에 대한 연결이 실패하면 마지막 연결 시도의 오류 메시지를
    포함한 실패 결과를 반환합니다.

    IP 주소 순서 정책은 다음과 같습니다.

    - prefer == "any":
      DNS에서 받은 원래 순서를 그대로 사용합니다.
    - prefer == "ipv4":
      IPv4 주소를 먼저 배치하고 IPv6 주소를 뒤에 배치합니다.
    - prefer == "ipv6":
      IPv6 주소를 먼저 배치하고 IPv4 주소를 뒤에 배치합니다.

    같은 IP 버전 내부에서는 원래 목록의 순서를 유지합니다.

    Args:
        ips: DNS 조회를 통해 얻은 IP 주소 목록입니다.
        port: 연결할 서버의 TCP 포트 번호입니다.
        timeout: 각 IP에 대한 연결 시도의 제한 시간입니다.
            단위는 초입니다.
        prefer: IP 주소 연결 우선순위입니다.
            "any", "ipv4", "ipv6" 중 하나를 사용합니다.

    Returns:
        TCPConnectResult 객체를 반환합니다.

        연결에 성공한 경우:
            - ip: 실제로 연결된 IP 주소
            - port: 연결한 포트 번호
            - connect_ms: 연결에 걸린 시간(ms)
            - local_addr: 로컬 소켓 주소
            - peer_addr: 연결된 서버의 소켓 주소
            - error: None
            - sock: 연결된 소켓 객체

        모든 연결이 실패한 경우:
            - ip: 마지막으로 연결을 시도한 IP 주소
            - port: 연결을 시도한 포트 번호
            - connect_ms: None
            - local_addr: None
            - peer_addr: None
            - error: 마지막 연결 오류 또는 기본 오류 메시지
            - sock: None

        ips가 비어 있는 경우에는 즉시 "No IPs to connect" 오류를
        포함한 결과를 반환합니다.
    """
    if not ips:
        return TCPConnectResult(
            ip=None,
            port=port,
            connect_ms=None,
            local_addr=None,
            peer_addr=None,
            error="No IPs to connect",
            sock=None,
        )

    ###########################################################
    # prefer 정책에 따라 IPv4와 IPv6 주소의 우선순위가 반영된
    # ordered 리스트를 만듭니다. 같은 버전 내부의 기존 순서는
    # 그대로 유지합니다.

    ipv4_ips = [ip for ip in ips if ":" not in ip]
    ipv6_ips = [ip for ip in ips if ":" in ip]

    if prefer == "ipv4":
        ordered = ipv4_ips + ipv6_ips
    elif prefer == "ipv6":
        ordered = ipv6_ips + ipv4_ips
    else:
        ordered = list(ips)

    ###########################################################

    last_err: Optional[str] = None

    for ip in ordered:
        ###########################################################
        # connect_one()을 호출하여 현재 IP에 연결을 시도합니다.
        # 실패하면 오류를 저장한 뒤 다음 IP로 넘어가고, 성공하면
        # 로컬 주소와 서버 주소를 추출하여 즉시 결과를 반환합니다.

        sock, connect_ms, error = connect_one(ip, port, timeout)

        if sock is None or error is not None:
            last_err = error
            continue

        try:
            local_addr = sock.getsockname()
            peer_addr = sock.getpeername()

            return TCPConnectResult(
                ip=ip,
                port=port,
                connect_ms=connect_ms,
                local_addr=local_addr,
                peer_addr=peer_addr,
                error=None,
                sock=sock,
            )
        except Exception as e:
            last_err = str(e)

            try:
                sock.close()
            except Exception:
                pass

        ###########################################################

    return TCPConnectResult(
        ip=ordered[-1] if ordered else None,
        port=port,
        connect_ms=None,
        local_addr=None,
        peer_addr=None,
        error=last_err or "All connections failed",
        sock=None,
    )