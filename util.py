import heapq

class PriorityQueue:
    """
    Implements a priority queue data structure. Each inserted item
    has a priority associated with it and the client is usually interested
    in quick retrieval of the lowest-priority item in the queue. This
    data structure allows O(1) access to the lowest-priority item.
    """

    def __init__(self):
        self.heap = []
        self.count = 0

    def push(self, item, priority):
        entry = (priority, self.count, item)
        heapq.heappush(self.heap, entry)
        self.count += 1

    def pop(self):
        priority, _, item = heapq.heappop(self.heap)
        return priority, item

    def isEmpty(self):
        return len(self.heap) == 0

    def update(self, item, priority):
        # If item already in priority queue with higher priority, update its priority and rebuild the heap.
        # If item already in priority queue with equal or lower priority, do nothing.
        # If item not in priority queue, do the same thing as self.push.
        for index, (p, c, i) in enumerate(self.heap):
            if i == item:
                if p <= priority:
                    break
                del self.heap[index]
                self.heap.append((priority, c, item))
                heapq.heapify(self.heap)
                break
        else:
            self.push(item, priority)

def get_neighbors(x, y, m, n):
    neighbors = [ (x-1,y), (x,y-1), (x,y+1), (x+1,y) ]
    neighbors = filter(lambda v: v[0] >= 0 and v[0] < n and v[1] >= 0 and v[1] < m, neighbors)
    return list(neighbors)

def get_cost(cost_map, v):
    C = cost_map[v[0]][v[1]]
    return C if C != None else 10000000


def dijkstra(source, dest, cost_map):

    m = len(cost_map[0])
    n = len(cost_map)

    def helper(visited, frontier):

        if frontier.isEmpty():
            return visited

        priority, (vertex, path) = frontier.pop()

        if vertex in visited:
            return helper(visited, frontier)

        visited[vertex] = (priority, path)

        if vertex == dest:
            return visited

        neighbors = get_neighbors(vertex[0], vertex[1], m, n)
        for neighbor in neighbors:
            if neighbor not in visited:
                frontier.push((neighbor, path+[vertex]), priority + get_cost(cost_map, neighbor))


        return helper(visited, frontier)

    frontier = PriorityQueue()
    frontier.push((source, []), 0)
    X = {}

    map = helper(X, frontier)

    return map[dest][1]

print(dijkstra((0,0),(2,3),[[2,3,1,6],[5,6,4,1],[7,2,3,8]]))
