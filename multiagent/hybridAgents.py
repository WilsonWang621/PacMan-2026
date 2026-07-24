"""
Optional hybrid Pacman agents.

This file is deliberately separate from the project answers in
``multiAgents.py``.  The standard Pacman launcher discovers files whose names
end in ``Agents.py``, so the agent can be selected without changing any of the
Berkeley framework:

    python pacman.py -p HybridPacmanAgent -a depth=2,dangerDepth=3

The controller combines three ideas:

* exact breadth-first maze distances for global food/capsule navigation;
* expectimax-style averaging for ordinary play;
* a pessimistic (minimax-style) component near active ghosts.

Only one action is returned on each turn, but all three signals contribute to
that decision.
"""

from collections import deque

from game import Agent, Directions


class _MazeDistanceCache:
    """Cache BFS distances without depending on the search project."""

    def __init__(self):
        self._walls = None
        self._distances = {}

    def reset_if_needed(self, walls):
        if self._walls is not walls:
            self._walls = walls
            self._distances = {}

    def from_point(self, start, walls):
        self.reset_if_needed(walls)
        start = (int(start[0]), int(start[1]))
        if start in self._distances:
            return self._distances[start]

        distances = {start: 0}
        fringe = deque([start])
        while fringe:
            x, y = fringe.popleft()
            for next_position in ((x + 1, y), (x - 1, y),
                                  (x, y + 1), (x, y - 1)):
                nx, ny = next_position
                if (0 <= nx < walls.width and 0 <= ny < walls.height
                        and not walls[nx][ny]
                        and next_position not in distances):
                    distances[next_position] = distances[(x, y)] + 1
                    fringe.append(next_position)

        self._distances[start] = distances
        return distances

    def distance(self, start, goal, walls):
        # Active ghosts and Pacman occupy grid points. Scared ghosts can be on
        # half-grid points, for which Manhattan distance is the useful fallback.
        if any(coordinate != int(coordinate)
               for coordinate in start + goal):
            return abs(start[0] - goal[0]) + abs(start[1] - goal[1])
        return self.from_point(start, walls).get(
            (int(goal[0]), int(goal[1])), float("inf")
        )


class HybridPacmanAgent(Agent):
    """
    Adaptive graph-search and adversarial/chance-search controller.

    ``risk`` is the minimum-outcome weight at ghost nodes.  It increases
    automatically when an active ghost is close, guarding against the overly
    optimistic uniform-ghost assumption used by plain expectimax.
    """

    def __init__(self, depth="2", dangerDepth="3", dangerRadius="auto",
                 risk="auto"):
        self.index = 0
        self.depth = int(depth)
        self.dangerDepth = int(dangerDepth)
        self.dangerRadius = (None if dangerRadius == "auto"
                             else float(dangerRadius))
        self.risk = None if risk == "auto" else float(risk)
        self._maze = _MazeDistanceCache()

    def getAction(self, gameState):
        legal_actions = gameState.getLegalActions(0)
        if not legal_actions:
            return Directions.STOP

        active_distance = self._closest_active_ghost(gameState)
        danger_radius = self._danger_radius(gameState)
        search_depth = (self.dangerDepth
                        if active_distance <= danger_radius
                        else self.depth)
        num_agents = gameState.getNumAgents()
        cache = {}

        def value(state, agent_index, completed_depth):
            key = (state, agent_index, completed_depth)
            if key in cache:
                return cache[key]
            if (completed_depth == search_depth
                    or state.isWin() or state.isLose()):
                result = self._evaluate(state)
                cache[key] = result
                return result

            actions = state.getLegalActions(agent_index)
            if not actions:
                result = self._evaluate(state)
                cache[key] = result
                return result

            next_agent = (agent_index + 1) % num_agents
            next_depth = completed_depth + (1 if next_agent == 0 else 0)
            child_values = [
                value(state.generateSuccessor(agent_index, action),
                      next_agent, next_depth)
                for action in actions
            ]

            if agent_index == 0:
                result = max(child_values)
            else:
                # Blend expected and worst-case outcomes. Directional ghosts
                # are neither uniformly random nor perfectly adversarial.
                expected = sum(child_values) / float(len(child_values))
                threat_distance = self._closest_active_ghost(state)
                local_risk = self._base_risk(state)
                if threat_distance <= 2:
                    local_risk = max(local_risk, 0.80)
                elif threat_distance <= 4:
                    local_risk = max(local_risk, 0.60)
                result = ((1.0 - local_risk) * expected
                          + local_risk * min(child_values))

            cache[key] = result
            return result

        next_agent = 1 % num_agents
        next_depth = 1 if next_agent == 0 else 0
        current_direction = gameState.getPacmanState().configuration.direction
        reverse = Directions.REVERSE[current_direction]
        scored_actions = []

        for action in legal_actions:
            successor = gameState.generateSuccessor(0, action)
            score = value(successor, next_agent, next_depth)
            if action == Directions.STOP:
                score -= 30
            elif action == reverse and len(legal_actions) > 2:
                score -= 2
            scored_actions.append((score, action))

        # Stable tie-breaking makes fixed-seed comparisons reproducible.
        return max(scored_actions, key=lambda item: item[0])[1]

    def _closest_active_ghost(self, state):
        pacman = state.getPacmanPosition()
        walls = state.getWalls()
        distances = [
            self._maze.distance(pacman, ghost.getPosition(), walls)
            for ghost in state.getGhostStates()
            if ghost.scaredTimer == 0
        ]
        return min(distances) if distances else float("inf")

    def _danger_radius(self, state):
        if self.dangerRadius is not None:
            return self.dangerRadius
        # Short, dense corridors give ghosts fewer escape branches, so search
        # deeper sooner. Larger layouts benefit from less conservative play.
        return 5.0 if state.getWalls().height <= 7 else 3.0

    def _base_risk(self, state):
        if self.risk is not None:
            return self.risk
        return 0.35 if state.getWalls().height <= 7 else 0.10

    def _evaluate(self, state):
        if state.isWin():
            return float("inf")
        if state.isLose():
            return -float("inf")

        pacman = state.getPacmanPosition()
        walls = state.getWalls()
        food = state.getFood().asList()
        capsules = state.getCapsules()
        score = state.getScore()

        # A*/BFS-style global navigation signal: exact wall-aware distance is
        # much more informative than Manhattan distance in winding corridors.
        food_distances = [
            self._maze.distance(pacman, target, walls) for target in food
        ]
        score -= 5.0 * len(food)
        if food_distances:
            nearest_food = min(food_distances)
            score -= 1.8 * nearest_food
            score += 10.0 / (nearest_food + 1.0)

        capsule_distances = [
            self._maze.distance(pacman, capsule, walls)
            for capsule in capsules
        ]
        score -= 18.0 * len(capsules)

        active_distances = []
        for ghost in state.getGhostStates():
            distance = self._maze.distance(
                pacman, ghost.getPosition(), walls
            )
            if ghost.scaredTimer > 0:
                if distance <= ghost.scaredTimer:
                    score += 120.0 / (distance + 1.0)
                    score += 3.0 * (ghost.scaredTimer - distance)
            else:
                active_distances.append(distance)
                if distance <= 1:
                    score -= 1000
                elif distance <= 2:
                    score -= 240
                elif distance <= 3:
                    score -= 70
                else:
                    score -= 10.0 / distance

        # Capsules become urgent only when there is an actual pursuer nearby.
        if (capsule_distances and active_distances
                and min(active_distances) <= self._danger_radius(state) + 1):
            score -= 2.5 * min(capsule_distances)

        score += 1.5 * (len(state.getLegalActions(0)) - 1)
        return score
