from __future__ import annotations

import socket
from typing import Optional


def resolve(host: str) -> tuple[list[str], Optional[str]]:
    """
    주어진 도메인 이름을 실제 통신에 사용할 수 있는 IP 주소 목록으로 변환합니다.

    socket.getaddrinfo()를 이용하여 host에 대응하는 주소 정보를 조회하고,
    각 조회 결과의 sockaddr에서 IP 주소만 추출합니다. 하나의 도메인에 대해
    같은 IP 주소가 여러 번 반환될 수 있으므로, 중복된 주소는 제거합니다.
    이때 DNS 조회 결과에서 처음 등장한 순서는 그대로 유지합니다.

    Args:
        host: 조회할 도메인 이름입니다.
            예: "google.com", "localhost"

    Returns:
        다음 두 값을 원소로 가지는 튜플을 반환합니다.

        - list[str]:
            중복이 제거된 IP 주소 목록입니다. IPv4와 IPv6 주소가 모두
            포함될 수 있으며, getaddrinfo()가 반환한 순서를 유지합니다.
        - Optional[str]:
            조회가 성공한 경우 None을 반환합니다. DNS 조회 중 예외가
            발생한 경우에는 빈 IP 목록과 함께 예외 메시지를 문자열로
            반환합니다.

    Examples:
        >>> ips, error = resolve("localhost")
        >>> error is None
        True
        >>> len(ips) >= 1
        True
    """
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)

        ###########################################################
        # sockaddr에서 IP 주소만 추출하여 리스트(ips)로 만듭니다.
        # 동일한 IP가 여러 번 등장할 수 있으므로 중복을 제거하되,
        # DNS 조회 결과에서 처음 등장한 순서는 그대로 유지합니다.

        ips: list[str] = []
        seen: set[str] = set()

        for info in infos:
            sockaddr = info[4]
            ip = sockaddr[0]

            if ip not in seen:
                seen.add(ip)
                ips.append(ip)

        ###########################################################

        return ips, None
    except Exception as e:
        return [], str(e)


def pick_ip(ips: list[str], prefer: str = "any") -> Optional[str]:
    """
    주어진 IP 주소 목록에서 prefer 정책에 맞는 주소 하나를 선택합니다.

    IPv4 주소는 주소 문자열에 콜론(:)이 없다는 점을 이용하여 구분하고,
    IPv6 주소는 주소 문자열에 콜론(:)이 포함된다는 점을 이용하여
    구분합니다.

    선택 정책은 다음과 같습니다.

    1. prefer가 "ipv4"인 경우:
       목록을 앞에서부터 확인하여 가장 먼저 발견되는 IPv4 주소를
       반환합니다.

    2. prefer가 "ipv6"인 경우:
       목록을 앞에서부터 확인하여 가장 먼저 발견되는 IPv6 주소를
       반환합니다.

    3. prefer가 "any"인 경우:
       IP 버전을 구분하지 않고 목록의 첫 번째 주소를 반환합니다.

    4. 선호하는 IP 버전의 주소가 없는 경우:
       사용 가능한 주소 중 첫 번째 주소를 반환합니다.

    5. IP 주소 목록이 비어 있는 경우:
       선택할 주소가 없으므로 None을 반환합니다.

    Args:
        ips: DNS 조회를 통해 얻은 IP 주소 목록입니다.
        prefer: 우선하여 선택할 IP 버전 정책입니다.
            "any", "ipv4", "ipv6" 중 하나를 사용합니다.

    Returns:
        정책에 따라 선택된 IP 주소를 반환합니다. 목록이 비어 있으면
        None을 반환합니다.

    Examples:
        >>> pick_ip(["2001:db8::1", "192.0.2.1"], "ipv4")
        '192.0.2.1'
        >>> pick_ip(["2001:db8::1", "192.0.2.1"], "ipv6")
        '2001:db8::1'
        >>> pick_ip([], "any") is None
        True
    """
    if not ips:
        return None

    ###########################################################
    # prefer 정책에 따라 IP 주소를 선택합니다.
    # 원하는 버전의 주소가 없다면 마지막에 ips[0]을 반환합니다.

    if prefer == "ipv4":
        for ip in ips:
            if ":" not in ip:
                return ip

    elif prefer == "ipv6":
        for ip in ips:
            if ":" in ip:
                return ip

    ###########################################################

    return ips[0]