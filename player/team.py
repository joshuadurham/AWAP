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
    IN_LINE = 3
    NO_STATE = 4

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
        self.AI_STATE = [(AI_STATE.NO_STATE, None), (AI_STATE.NO_STATE, None), (AI_STATE.NO_STATE, None), (AI_STATE.NO_STATE, None)]
        
        ### PARAMETERS
        self.threshold = 1

        self.value_map = valueMap
        self.team_size = team_size
        self.team_name = 'Al-bro-rithms'

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


        ### TODO: UPDATE AI STATE
        newAIState = []

        self.AI_STATE = newAIState
        self.prev_score = score
        self.prev_line_states = playerLinePos
        return [Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT]
