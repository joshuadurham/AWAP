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

        for yIdx in range(len(initial_board)):
            for xIdx in range(len(initial_board[0])):
                tile = initial_board[yIdx][xIdx]
                if(tile.get_booth() is not None):
                    boothSquares[tile.get_booth()].append((xIdx,yIdx))
                if(tile.get_line() is not None):
                    lineSquares[tile.get_line()].append((xIdx,yIdx))
                print(tile.is_end_of_line())
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
                self.cost_map[boothY][boothX] = None
            for (lineX, lineY) in self.line_squares[company]:
                valueMap[lineY][lineX] = companyPoints[company]

        self.prev_line_states = [-1,-1,-1,-1]
        self.ai_state = [(AI_STATE.NO_STATE, None), (AI_STATE.NO_STATE, None), (AI_STATE.NO_STATE, None), (AI_STATE.NO_STATE, None)]
        
        ### PARAMETERS
        self.threshold = 1

        self.value_map = valueMap
        self.team_size = team_size
        self.team_name = 'Al-bro-rithms'
        self.blacklist = initial_board
        for i in range(len(self.blacklist)):
            for j in range(len(self.blacklist[0])):
                self.blacklist[i][j] = 0
        
    def fuzzy_enter_line(self, state, arr, x, y):
        # Tries to enter line at x,y
        tile = arr[x][y]
        company = tile.get_line()
        if not tile.is_visible():
            return None
        if tile.is_end_of_line():
            return (x,y)
        else:
            for i in range(x-1, x+2):
                for j in range(y-1, y+2):
                    if abs(i+j - x-y) != 1:
                        continue
                    if arr[i][j].is_end_of_line() and arr[i][j].is_visible() and arr[i][j].get_line() == company:
                        return (i,j)
        return None
    def get_lin_dir(x, y, i, j):
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
        if arr[state.x, state.y].is_end_of_line():
            return Direction.ENTER
        else:
            i = self.fuzzy_enter_line(state, arr, state.x, state.y)
            if i is None:
                return None
            else:
                return get_lin_dir((state.x, state.y), i)

    def should_i_stay(self, state, arr):
        s = state.line_pos
        if s == -1:
            return None
        points = self.company_points[arr[state.x][state.y].get_line()]
        if points/s < threshold:
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
                companyName = self.board[yCoord][xCoord]
                self.company_points[companyName] = self.company_points[companyName]//2
                lineCoords = self.line_squares[companyName]
                for (lineXCoord, lineYCoord) in lineCoords:
                    self.value_map[lineYCoord, lineXCoord] = self.company_points[companyName]

        # Update cost map based on current visibility
        for yIdx in range(len(visible_board)):
            for xIdx in range(len(visible_board[0])):
                tile = visible_board[yIdx][xIdx]
                if(self.cost_map[yIdx][xIdx] is not None and tile.is_visible()):
                    (currCost, currCount) = self.cost_map[yIdx][xIdx]
                    self.cost_map[yIdx][xIdx] = (currCost + tile.get_threshold(), currCount + 1)

        newAIState = []

        for stateIdx in range(len(self.ai_state)):
            (state, position) = self.ai_state[stateIdx]
            newState = AI_STATE.NO_STATE
            if(state == AI_STATE.NO_STATE):
                newState = AI_STATE.LONG_DIST_EXPL
                (goalX, goalY) = getOptPosition()
                newAIState.append((newState, (goalX, goalY)))
            elif (state == AI_STATE.NAV_TO_CLOSE):
                (goalX, goalY) = position
                (playerX, playerY) = playerCoord[stateIdx]
                if(playerX == goalX and playerY == goalY):
                    newState = AI_STATE.NAV_TO_CLOSE
                    newAIState.append((newState, None))
                else:
                    newAIState.append((state, position))
            elif (state == AI_STATE.ENTERING_LINE):
                currentLineState = playerLinePos[stateIdx]
                if(currentLineState >= 0):
                    newState = AI_STATE.IN_LINE
                    newAIState.append((newState, None))
                else:
                    newAIState.append((state, None))
            elif(state == AI_STATE.IN_LINE):
                currentLineState = playerLinePos[stateIdx]
                if (currentLineState == -1 or not self.should_i_stay(states[stateIdx], visible_board)):
                    newState = AI_STATE.LONG_DIST_EXPL
                    (goalX, goalY) = getOptPosition()
                    newAIState.append((newState, (goalX, goalY)))
                else:
                    newAIState.append((state, None))
            else:
                if(self.should_enter_line(visible_board, states[stateIdx]) is not None):
                    newState = AI_STATE.NAV_TO_CLOSE
                    (goalX, goalY) = self.should_enter_line(visible_board, states[stateIdx])
                    newAIState.append((newState, (goalX, goalY)))
                else:
                    newAIState.append((state, position))

        self.AI_STATE = newAIState
        self.prev_score = score
        self.prev_line_states = playerLinePos
        return [Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT]
