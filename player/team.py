"""
The team.py file is where you should write all your code!

Write the __init__ and the step functions. Further explanations
about these functions are detailed in the wiki.

List your Andrew ID's up here!
jbdurham
sayanc
sdave
ariedelm
"""
from awap2019 import Tile, Direction, State
from enum import Enum
from player.util import dijkstra
import numpy as np
from numpy import unravel_index
class AI_STATE(Enum):
    LONG_DIST_EXPL = 1
    NAV_TO_CLOSE = 2
    ENTERING_LINE=3
    IN_LINE = 4
    NO_STATE = 5

class Team(object):
    def __init__(self, initial_board, team_size, company_info):
        """
        The initializer is for you to precompute anything from the
        initial board and the company information! Feel free to create any
        new instance variables to help you out.

        Specific information about initial_board and company_info are
        on the wiki. team_size, although passed to you as a parameter, will
        always be 4.
        """
        companyNames = []
        mapWidth = len(initial_board[0])
        mapHeight = len(initial_board)
        companyPoints = {}
        boothSquares = {}
        lineSquares = {}
        for company in company_info:
            companyNames.append(company)
        self.company_names = companyNames
        for company in companyNames:
            companyPoints[company] = company_info[company]
            boothSquares[company] = []
            lineSquares[company] = []
        self.company_points = company_info

        for yIdx in range(len(initial_board[0])):
            for xIdx in range(len(initial_board)):
                tile = initial_board[xIdx][yIdx]
                if(tile.get_booth() is not None):
                    boothSquares[tile.get_booth()].append((xIdx,yIdx))
                if(tile.get_line() is not None):
                    lineSquares[tile.get_line()].append((xIdx,yIdx))
        self.board = initial_board
        self.booth_squares = boothSquares
        self.line_squares = lineSquares

        costMap = []
        for yIdx in range(mapHeight):
            nextRow = []
            for xIdx in range(mapWidth):
                # (Total sum of costs, number of readings)
                nextRow.append((1,1))
            costMap.append(nextRow)

        self.cost_map = costMap

        valueMap = []
        for yIdx in range(mapHeight):
            nextRow = []
            for xIdx in range(mapWidth):
                nextRow.append(0)
            valueMap.append(nextRow)

        for company in companyNames:
            for (boothX, boothY) in self.booth_squares[company]:
                self.cost_map[boothX][boothY] = None
            for (lineX, lineY) in self.line_squares[company]:
                valueMap[lineX][lineY] = companyPoints[company]

        self.prev_line_states = [-1,-1,-1,-1]
        self.ai_state = [(AI_STATE.NO_STATE, None), (AI_STATE.NO_STATE, None), (AI_STATE.NO_STATE, None), (AI_STATE.NO_STATE, None)]
        
        ### PARAMETERS
        self.threshold = 5

        self.value_map = valueMap
        self.team_size = team_size
        self.team_name = 'Al-bro-rithms'
        blacklist = []
        for yIdx in range(mapHeight):
            nextRow = []
            for xIdx in range(mapWidth):
                nextRow.append(0)
            blacklist.append(nextRow)
        self.blacklist = blacklist

    def get_dest(self, agent=None):
        m = len(self.value_map)
        n = len(self.value_map[0])

        if agent == None:
            a = np.array(self.value_map)
            res = list(unravel_index(a.argmax(), a.shape))
            if (res[0] >= len(self.cost_map)):
                res[0] = self.line_squares[self.company_names[0]][0][0]
            if (res[1] >= len(self.cost_map[0])):
                res[1] = self.line_squares[self.company_names[0]][0][1]
            return tuple(res)
        else:
            value_map_tl = (np.array(list(map(lambda v: v[:n//2], self.value_map[:m//2]))), 0, 0)
            value_map_tr = (np.array(list(map(lambda v: v[n//2:], self.value_map[:m//2]))), n//2, 0)
            value_map_bl = (np.array(list(map(lambda v: v[:n//2], self.value_map[m//2:]))), 0, m//2)
            value_map_br = (np.array(list(map(lambda v: v[n//2:], self.value_map[m//2:]))), n//2, m//2)

            value_maps = sorted([value_map_tl, value_map_tr, value_map_bl, value_map_br], key=lambda v: v[0].max(), reverse=True)

            x, y = unravel_index(value_maps[agent][0].argmax(), value_maps[agent][0].shape)
            res = [x + value_maps[agent][1], y + value_maps[agent][2]]
            if (res[0] >= len(self.cost_map)):
                res[0] = self.line_squares[self.company_names[0]][0][0]
            if (res[1] >= len(self.cost_map[0])):
                res[1] = self.line_squares[self.company_names[0]][0][1]
            return tuple(res)
        
    def fuzzy_enter_line(self, state, arr, x, y):
        # Tries to enter line at x,y
        tile = arr[x][y]
        company = tile.get_line()
        if not tile.is_visible():
            return None
        if tile.is_end_of_line():
            return (x,y)
        else:
            for i in range(max(x-2, 0), min(x+3, len(arr))):
                for j in range(max(y-2, 0), min(y+3, len(arr[0]))):
                    if abs(i+j - x-y) != 1:
                        continue
                    if arr[i][j].is_end_of_line() and arr[i][j].is_visible() and arr[i][j].get_line() == company:
                        return (i,j)
        return None
    def get_lin_dir(self, x, y, i, j):
        diffx = i-x
        diffy = j-y
        if diffx < 0:
            return Direction.UP
        if diffx > 0:
            return Direction.DOWN
        if diffy < 0:
            return Direction.LEFT
        if diffy > 0:
            return Direction.RIGHT
        return Direction.NONE

    def enter_line(self, state, arr):
        if arr[state.x][state.y].is_end_of_line():
            return Direction.ENTER
        else:
            i = self.fuzzy_enter_line(state, arr, state.x, state.y)
            if i is None:
                return None
            else:
                return self.get_lin_dir(state.x, state.y, i[0], i[1])

    def should_i_stay(self, state, arr):
        s = state.line_pos
        if s == -1:
            return None
        points = self.company_points[arr[state.x][state.y].get_line()]
        if points/(s+1) < self.threshold:
            self.blacklist[state.x][state.y] = 10
            return False
        return True
    def should_enter_line(self, arr, state):
        """
        Determines if bots should enter nearby line, based on lower-bounding
        length and using threshold basis for optimality
        """
        # self.threshold = 2
        # def line_cost(x, y):
        #     # Given line tile at x and y, determines how worthwhile line is
        #     # cost/(length_of_line).
        #     tile = arr[x][y]
        #     company = tile.get_line()
        #     if company is None:
        #         return ("NO", -1, 1)
        #     startx,starty = (0,0) #self.company_line_starts[company]
        #     numpeeps = tile.get_num_bots()
        #     if numpeeps == 0:
        #         totleng = (3*(abs(startx-x) + abs(starty-y)), "l") #one is zero
        #     elif numpeeps == 3:
        #         totleng = (3*(abs(startx-x) + abs(starty-y) + 1), "g")
        #     else:
        #         totleng = (3*(abs(startx-x) + abs(starty-y)) + numpeeps, "e")
        #     value = self.company_points[company]
        #     if((totleng[1] == "g" or totleng[1] == "e")
        #        and value/totleng[0] <= self.threshold):
        #        return ("NO", totleng, value)
        #     if((totleng[1] == "l" or totleng[1] == "e")
        #        and value/totleng[0] > self.threshold):
        #        return ("YES", totleng, value)
        #     return ("MAYBE", totleng, value)

        maxval = 0
        maxxy = None
        if state.progress != 0 or state.line_pos != -1:
            return maxxy
        x,y = state.x, state.y
        for tilex in range(max(x-2, 0), min(x+3, len(arr))):
            for tiley in range(max(y-2, 0), min(y+3, len(arr[0]))):
                #Represents visible tiles for this bot
                #If one is a line tile, figure out which line, estimate how
                #long the line is, decide if worthwhile
                tile = arr[tilex][tiley]
                if(tile.is_end_of_line() and self.blacklist[tilex][tiley]==0):
                    if self.company_points[tile.get_line()] > maxval:
                        maxxy = (tilex,tiley)
                        maxval = self.company_points[tile.get_line()]
        return maxxy
    def step(self, visible_board, states, score):
        """
        The step function should return a list of four Directions.

        For more information on what visible_board, states, and score
        are, please look on the wiki.
        """
        playerDirections = []
        playerIDs = []
        playerCoord = []
        playerProgress = []
        playerThreshold = []
        playerLinePos = []
        for stateIdx in range(len(states)):
            state = states[stateIdx]
            playerDirections.append(state.dir)
            playerIDs.append(state.id)
            playerCoord.append((state.x, state.y))
            playerProgress.append(state.progress)
            playerThreshold.append(state.threshold)
            playerLinePos.append(state.line_pos)

        for linePosIdx in range(len(playerLinePos)):
            oldLinePos = self.prev_line_states[linePosIdx]
            currLinePos = playerLinePos[linePosIdx]
            if (oldLinePos == 0 and currLinePos == -1):
                (xCoord, yCoord) = playerCoord[linePosIdx]
                companyName = self.board[xCoord][yCoord].get_line()
                if (companyName is None):
                    companyName = self.company_names[0]
                self.company_points[companyName] = self.company_points[companyName]//2
                lineCoords = self.line_squares[companyName]
                for (lineXCoord, lineYCoord) in lineCoords:
                    self.value_map[lineXCoord][lineYCoord] = self.company_points[companyName]

        # Update cost map based on current visibility
        for yIdx in range(len(visible_board[0])):
            for xIdx in range(len(visible_board)):
                tile = visible_board[xIdx][yIdx]
                if(self.cost_map[xIdx][yIdx] is not None and tile.is_visible()):
                    (currCost, currCount) = self.cost_map[xIdx][yIdx]
                    self.cost_map[xIdx][yIdx] = (currCost + tile.get_threshold(), currCount + 1)

        newAIState = []

        def convert_path_to_dir(path):
            result = []
            for i in range(len(path[:-1])):
                result.append(Direction.get_dir(path[i], path[i+1]))
            return result

        for stateIdx in range(len(self.ai_state)):
            (state, position) = self.ai_state[stateIdx]
            newState = AI_STATE.NO_STATE
            if(state == AI_STATE.NO_STATE):
                newState = AI_STATE.LONG_DIST_EXPL
                (goalX, goalY) = self.get_dest(stateIdx)
                newAIState.append((newState, (goalX, goalY)))
            elif (state == AI_STATE.NAV_TO_CLOSE):
                (goalX, goalY) = position
                (playerX, playerY) = playerCoord[stateIdx]
                if(playerX == goalX and playerY == goalY):
                    newState = AI_STATE.ENTERING_LINE
                    newAIState.append((newState, None))
                else:
                    newAIState.append((state, position))
            elif (state == AI_STATE.ENTERING_LINE):
                currentLineState = playerLinePos[stateIdx]
                if(self.enter_line(states[stateIdx], visible_board) is None):
                    newState = AI_STATE.LONG_DIST_EXPL
                    newAIState.append((newState, self.get_dest()))
                elif(currentLineState >= 0):
                    newState = AI_STATE.IN_LINE
                    newAIState.append((newState, None))
                else:
                    newAIState.append((state, None))
            elif(state == AI_STATE.IN_LINE):
                currentLineState = playerLinePos[stateIdx]
                if (currentLineState == -1 or not self.should_i_stay(states[stateIdx], visible_board)):
                    newState = AI_STATE.LONG_DIST_EXPL
                    (goalX, goalY) = self.get_dest()
                    newAIState.append((newState, (goalX, goalY)))
                else:
                    newAIState.append((state, None))
            else:
                (currX, currY) = playerCoord[stateIdx]
                (goalX, goalY) = position
                if(self.should_enter_line(visible_board, states[stateIdx]) is not None):
                    newState = AI_STATE.NAV_TO_CLOSE
                    (goalX, goalY) = self.should_enter_line(visible_board, states[stateIdx])
                    newAIState.append((newState, (goalX, goalY)))
                elif(currX == goalX and currY == goalY):
                    (newX, newY) = self.get_dest()
                    newAIState.append((state, (newX, newY)))
                else:
                    newAIState.append((state, position))
            
        finalCommands = []

        for stateIdx in range(len(newAIState)):
            (state, position) = newAIState[stateIdx]
            if(state == AI_STATE.NO_STATE):
                #SHOULD NEVER HAVE THIS
                finalCommands.append(Direction.UP)
            if (state == AI_STATE.NAV_TO_CLOSE):
                prevDir = playerDirections[stateIdx]
                currProgress = playerProgress[stateIdx]
                currThreshold = playerThreshold[stateIdx]
                numMoreMoves = currThreshold - currProgress
                if (currProgress == 0):
                    (currX, currY) = playerCoord[stateIdx]
                    (goalX, goalY) = position
                    if (currX == goalX and currY == goalY):
                        newAIState[stateIdx] = (AI_STATE.ENTERING_LINE, None)
                    else:
                        fullPathFromDij = dijkstra((currX, currY), position, self.cost_map)
                        listOfDirs = convert_path_to_dir(fullPathFromDij)
                        nextMove = listOfDirs[0]
                        finalCommands.append(nextMove)
                else:
                    finalCommands.append(prevDir)
            if (state == AI_STATE.ENTERING_LINE):
                directionToCommand = self.enter_line(states[stateIdx], visible_board)
                finalCommands.append(directionToCommand)
            if(state == AI_STATE.IN_LINE):
                finalCommands.append(Direction.NONE)
            else:
                prevDir = playerDirections[stateIdx]
                currProgress = playerProgress[stateIdx]
                currThreshold = playerThreshold[stateIdx]
                numMoreMoves = currThreshold - currProgress
                if (currProgress == 0):
                    (currX, currY) = playerCoord[stateIdx]
                    if (position is None):
                        newPosition = self.line_squares[self.company_names[0]][0]
                        position = newPosition
                    (goalX, goalY) = position
                    if(currX == goalX and currY == goalY):
                        finalCommands.append(Direction.NONE)
                        newAIState[stateIdx] = (AI_STATE.ENTERING_LINE, None)
                    else:
                        fullPathFromDij = dijkstra((currX, currY), position, self.cost_map)
                        listOfDirs = convert_path_to_dir(fullPathFromDij)
                        nextMove = listOfDirs[0]
                        finalCommands.append(nextMove)
                else:
                    finalCommands.append(prevDir)

        self.ai_state = newAIState
        self.prev_score = score
        self.prev_line_states = playerLinePos
        return finalCommands
