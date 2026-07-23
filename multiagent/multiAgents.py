# multiAgents.py
# --------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from util import manhattanDistance
from game import Directions
import random, util

from game import Agent
from pacman import GameState

class ReflexAgent(Agent):
    """
    A reflex agent chooses an action at each choice point by examining
    its alternatives via a state evaluation function.

    The code below is provided as a guide.  You are welcome to change
    it in any way you see fit, so long as you don't touch our method
    headers.
    """


    def getAction(self, gameState: GameState):
        """
        You do not need to change this method, but you're welcome to.

        getAction chooses among the best options according to the evaluation function.

        Just like in the previous project, getAction takes a GameState and returns
        some Directions.X for some X in the set {NORTH, SOUTH, WEST, EAST, STOP}
        """
        # Collect legal moves and successor states
        legalMoves = gameState.getLegalActions()

        # Choose one of the best actions
        scores = [self.evaluationFunction(gameState, action) for action in legalMoves]
        bestScore = max(scores)
        bestIndices = [index for index in range(len(scores)) if scores[index] == bestScore]
        chosenIndex = random.choice(bestIndices) # Pick randomly among the best

        "Add more of your code here if you want to"

        return legalMoves[chosenIndex]

    def evaluationFunction(self, currentGameState: GameState, action):
        """
        Design a better evaluation function here.

        The evaluation function takes in the current and proposed successor
        GameStates (pacman.py) and returns a number, where higher numbers are better.

        The code below extracts some useful information from the state, like the
        remaining food (newFood) and Pacman position after moving (newPos).
        newScaredTimes holds the number of moves that each ghost will remain
        scared because of Pacman having eaten a power pellet.

        Print out these variables to see what you're getting, then combine them
        to create a masterful evaluation function.
        """
        # Useful information you can extract from a GameState (pacman.py)
        successorGameState = currentGameState.generatePacmanSuccessor(action)
        newPos = successorGameState.getPacmanPosition()
        newFood = successorGameState.getFood()
        newGhostStates = successorGameState.getGhostStates()
        newScaredTimes = [ghostState.scaredTimer for ghostState in newGhostStates]

        if successorGameState.isWin():
            return float('inf')
        if successorGameState.isLose():
            return -float('inf')

        score = successorGameState.getScore()
        foodPositions = newFood.asList()
        if foodPositions:
            closestFood = min(manhattanDistance(newPos, food)
                              for food in foodPositions)
            score += 12.0 / (closestFood + 1)
        score -= 4 * len(foodPositions)
        score -= 15 * len(successorGameState.getCapsules())

        for ghostState, scaredTime in zip(newGhostStates, newScaredTimes):
            distance = manhattanDistance(newPos, ghostState.getPosition())
            if scaredTime > 0:
                if distance <= scaredTime:
                    score += 50.0 / (distance + 1)
            else:
                if distance == 0:
                    return -float('inf')
                score -= 8.0 / distance
                if distance <= 1:
                    score -= 200

        if action == Directions.STOP:
            score -= 10
        return score

def scoreEvaluationFunction(currentGameState: GameState):
    """
    This default evaluation function just returns the score of the state.
    The score is the same one displayed in the Pacman GUI.

    This evaluation function is meant for use with adversarial search agents
    (not reflex agents).
    """
    return currentGameState.getScore()

class MultiAgentSearchAgent(Agent):
    """
    This class provides some common elements to all of your
    multi-agent searchers.  Any methods defined here will be available
    to the MinimaxPacmanAgent, AlphaBetaPacmanAgent & ExpectimaxPacmanAgent.

    You *do not* need to make any changes here, but you can if you want to
    add functionality to all your adversarial search agents.  Please do not
    remove anything, however.

    Note: this is an abstract class: one that should not be instantiated.  It's
    only partially specified, and designed to be extended.  Agent (game.py)
    is another abstract class.
    """

    def __init__(self, evalFn = 'scoreEvaluationFunction', depth = '2'):
        self.index = 0 # Pacman is always agent index 0
        self.evaluationFunction = util.lookup(evalFn, globals())
        self.depth = int(depth)

class MinimaxAgent(MultiAgentSearchAgent):
    """
    Your minimax agent (question 2)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the minimax action from the current gameState using self.depth
        and self.evaluationFunction.

        Here are some method calls that might be useful when implementing minimax.

        gameState.getLegalActions(agentIndex):
        Returns a list of legal actions for an agent
        agentIndex=0 means Pacman, ghosts are >= 1

        gameState.generateSuccessor(agentIndex, action):
        Returns the successor game state after an agent takes an action

        gameState.getNumAgents():
        Returns the total number of agents in the game

        gameState.isWin():
        Returns whether or not the game state is a winning state

        gameState.isLose():
        Returns whether or not the game state is a losing state
        """
        numAgents = gameState.getNumAgents()

        def value(state, agentIndex, depth):
            if depth == self.depth or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            legalActions = state.getLegalActions(agentIndex)
            if not legalActions:
                return self.evaluationFunction(state)

            nextAgent = (agentIndex + 1) % numAgents
            nextDepth = depth + 1 if nextAgent == 0 else depth
            childValues = [
                value(state.generateSuccessor(agentIndex, action),
                      nextAgent, nextDepth)
                for action in legalActions
            ]
            if agentIndex == 0:
                return max(childValues)
            return min(childValues)

        legalActions = gameState.getLegalActions(0)
        if not legalActions:
            return Directions.STOP

        nextAgent = 1 % numAgents
        nextDepth = 1 if nextAgent == 0 else 0
        bestAction = legalActions[0]
        bestValue = -float('inf')
        for action in legalActions:
            successor = gameState.generateSuccessor(0, action)
            successorValue = value(successor, nextAgent, nextDepth)
            if successorValue > bestValue:
                bestValue = successorValue
                bestAction = action
        return bestAction

class AlphaBetaAgent(MultiAgentSearchAgent): # Minimax 返回值 = Alpha-Beta 返回值 理论上二者的最优动作价值相同，但 Alpha-Beta 通常生成更少的后继状态。
    """
    Your minimax agent with alpha-beta pruning (question 3)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the minimax action using self.depth and self.evaluationFunction
        """
        numAgents = gameState.getNumAgents()

        def value(state, agentIndex, depth, alpha, beta):
            if depth == self.depth or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            legalActions = state.getLegalActions(agentIndex)
            if not legalActions:
                return self.evaluationFunction(state)

            nextAgent = (agentIndex + 1) % numAgents
            nextDepth = depth + 1 if nextAgent == 0 else depth

            if agentIndex == 0:
                result = -float('inf')
                for action in legalActions:
                    successor = state.generateSuccessor(agentIndex, action)
                    result = max(
                        result,
                        value(successor, nextAgent, nextDepth, alpha, beta)
                    )
                    if result > beta:
                        return result
                    alpha = max(alpha, result)
                return result

            result = float('inf')
            for action in legalActions:
                successor = state.generateSuccessor(agentIndex, action)
                result = min(
                    result,
                    value(successor, nextAgent, nextDepth, alpha, beta)
                )
                if result < alpha:
                    return result
                beta = min(beta, result)
            return result

        legalActions = gameState.getLegalActions(0)
        if not legalActions:
            return Directions.STOP

        nextAgent = 1 % numAgents
        nextDepth = 1 if nextAgent == 0 else 0
        alpha, beta = -float('inf'), float('inf')
        bestAction = legalActions[0]
        bestValue = -float('inf')
        for action in legalActions:
            successor = gameState.generateSuccessor(0, action)
            successorValue = value(
                successor, nextAgent, nextDepth, alpha, beta
            )
            if successorValue > bestValue:
                bestValue = successorValue
                bestAction = action
            alpha = max(alpha, bestValue)
        return bestAction

class ExpectimaxAgent(MultiAgentSearchAgent):
    """
      Your expectimax agent (question 4)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the expectimax action using self.depth and self.evaluationFunction

        All ghosts should be modeled as choosing uniformly at random from their
        legal moves.
        """
        numAgents = gameState.getNumAgents()

        def value(state, agentIndex, depth):
            if depth == self.depth or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            legalActions = state.getLegalActions(agentIndex)
            if not legalActions:
                return self.evaluationFunction(state)

            nextAgent = (agentIndex + 1) % numAgents
            nextDepth = depth + 1 if nextAgent == 0 else depth
            childValues = [
                value(state.generateSuccessor(agentIndex, action),
                      nextAgent, nextDepth)
                for action in legalActions
            ]
            if agentIndex == 0:
                return max(childValues)
            return sum(childValues) / float(len(childValues))

        legalActions = gameState.getLegalActions(0)
        if not legalActions:
            return Directions.STOP

        nextAgent = 1 % numAgents
        nextDepth = 1 if nextAgent == 0 else 0
        bestAction = legalActions[0]
        bestValue = -float('inf')
        for action in legalActions:
            successor = gameState.generateSuccessor(0, action)
            successorValue = value(successor, nextAgent, nextDepth)
            if successorValue > bestValue:
                bestValue = successorValue
                bestAction = action
        return bestAction

def betterEvaluationFunction(currentGameState: GameState):
    """
    Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable
    evaluation function (question 5).

    Combines the game score with food, capsule, and ghost-distance features.
    Active ghosts are treated as threats, while reachable scared ghosts are
    treated as opportunities.
    """
    if currentGameState.isWin():
        return float('inf')
    if currentGameState.isLose():
        return -float('inf')

    pacmanPosition = currentGameState.getPacmanPosition()
    score = currentGameState.getScore()

    foodPositions = currentGameState.getFood().asList()
    score -= 4 * len(foodPositions)
    if foodPositions:
        closestFood = min(manhattanDistance(pacmanPosition, food)
                          for food in foodPositions)
        score -= 1.5 * closestFood
        score += 8.0 / (closestFood + 1)

    capsules = currentGameState.getCapsules()
    score -= 15 * len(capsules)
    if capsules:
        closestCapsule = min(manhattanDistance(pacmanPosition, capsule)
                             for capsule in capsules)
        score -= closestCapsule

    for ghostState in currentGameState.getGhostStates():
        distance = manhattanDistance(
            pacmanPosition, ghostState.getPosition()
        )
        if ghostState.scaredTimer > 0:
            if distance <= ghostState.scaredTimer:
                score += 40.0 / (distance + 1)
                score += 2 * (ghostState.scaredTimer - distance)
        else:
            if distance == 0:
                return -float('inf')
            score -= 6.0 / distance
            if distance <= 1:
                score -= 250
            elif distance <= 2:
                score -= 80

    return score

# Abbreviation
better = betterEvaluationFunction
