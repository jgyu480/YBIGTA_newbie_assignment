from __future__ import annotations
from collections import deque


"""
TODO:
- rotate_and_remove 구현하기 
"""


def create_circular_queue(n: int) -> deque[int]:
    """1부터 n까지의 숫자로 deque를 생성합니다."""
    return deque(range(1, n + 1))


def rotate_and_remove(queue: deque[int], k: int) -> int:
    """
    큐에서 k번째 원소를 제거하고 반환합니다.
    """
    # 구현하세요!
    for _ in range(k - 1):
        queue.append(queue.popleft())

    return queue.popleft()


"""
TODO:
- josephus_problem 구현하기
    # 요세푸스 문제 구현
        # 1. 큐 생성
        # 2. 큐가 빌 때까지 반복
        # 3. 제거 순서 리스트 반환
"""


def josephus_problem(n: int, k: int) -> list[int]:
    """
    요세푸스 문제를 해결합니다.
    1부터 n까지의 원소가 들어 있는 큐에서 k번째 원소를 반복해서 제거하고,
    제거된 원소들의 순서를 리스트로 반환합니다.
    """
    # 구현하세요!
    queue = create_circular_queue(n)
    result: list[int] = []

    while queue:
        removed = rotate_and_remove(queue, k)
        result.append(removed)

    return result


def solve_josephus() -> None:
    """입, 출력 format"""
    n: int
    k: int
    n, k = map(int, input().split())
    result: list[int] = josephus_problem(n, k)
    
    # 출력 형식: <3, 6, 2, 7, 5, 1, 4>
    print("<" + ", ".join(map(str, result)) + ">")


if __name__ == "__main__":
    solve_josephus()