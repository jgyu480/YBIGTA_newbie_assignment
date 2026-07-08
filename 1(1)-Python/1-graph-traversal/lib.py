from __future__ import annotations
import copy
from collections import deque
from collections import defaultdict
from typing import DefaultDict, List


"""
TODO:
- __init__ 구현하기
- add_edge 구현하기
- dfs 구현하기 (재귀 또는 스택 방식 선택)
- bfs 구현하기
"""


class Graph:
    def __init__(self, n: int) -> None:
        """
        정점 개수 n을 입력받아 그래프를 초기화한다.
        정점 번호는 1번부터 n번까지 사용하며,
        각 정점의 인접 정점을 저장할 인접 리스트를 만든다.
        """
        self.n = n
        self.graph: DefaultDict[int, list[int]] = defaultdict(list)

    
    def add_edge(self, u: int, v: int) -> None:
        """
        두 정점 u와 v를 입력받아 양방향 간선을 추가한다.
        u의 인접 리스트에는 v를 추가하고,
        v의 인접 리스트에는 u를 추가한다.
        """
        self.graph[u].append(v)
        self.graph[v].append(u)
    
    def dfs(self, start: int) -> list[int]:
        """
        시작 정점 start를 입력받아 깊이 우선 탐색을 수행한다.
        방문 가능한 정점이 여러 개라면 번호가 작은 정점부터 방문한다.
        탐색이 끝나면 방문한 정점 번호들을 순서대로 담은 리스트를 반환한다.
        """
        visited: list[bool] = [False] * (self.n + 1)
        result: list[int] = []

        for node in self.graph:
            self.graph[node].sort()

        def _dfs(now: int) -> None:
            visited[now] = True
            result.append(now)

            for nxt in self.graph[now]:
                if not visited[nxt]:
                    _dfs(nxt)

        _dfs(start)
        return result
    
    def bfs(self, start: int) -> list[int]:
        """
        시작 정점 start를 입력받아 너비 우선 탐색을 수행한다.
        큐를 사용하여 가까운 정점부터 방문하며,
        방문 가능한 정점이 여러 개라면 번호가 작은 정점부터 방문한다.
        탐색이 끝나면 방문한 정점 번호들을 순서대로 담은 리스트를 반환한다.
        """
        visited: list[bool] = [False] * (self.n + 1)
        result: list[int] = []

        for node in self.graph:
            self.graph[node].sort()

        q: deque[int] = deque([start])
        visited[start] = True

        while q:
            now: int = q.popleft()
            result.append(now)

            for nxt in self.graph[now]:
                if not visited[nxt]:
                    visited[nxt] = True
                    q.append(nxt)

        return result
    
    def search_and_print(self, start: int) -> None:
        """
        시작 정점 start를 입력받아 DFS와 BFS를 각각 수행한다.
        첫 번째 줄에는 DFS 방문 순서를 출력하고,
        두 번째 줄에는 BFS 방문 순서를 출력한다.
        """
        dfs_result = self.dfs(start)
        bfs_result = self.bfs(start)
        
        print(' '.join(map(str, dfs_result)))
        print(' '.join(map(str, bfs_result)))