from utils.PlaceFinder import *
from utils.RobotArm import *
from utils.Nodes import *
from utils.AStar import *
import numpy as np
import sys

import copy as cp

"""
TODO :
    - define mecanical constraints
    - find a better way to generate the path
"""


class Solver(PlaceFinder, AStar):
    def __init__(self, shelf_size_x, shelf_size_y, precision, graph, goal):
        """ This class permits to find the right strategy to reach the goal object without touching any other object.

        Args:
            shelf_size_x (int): x size of the shelf in mm
            shelf_size_y (int): y size of the shelf in mm
            precision (int): number of mm per pixel
        """
        self.__graph = graph
        self.goal = goal

        self.objectRadiusProximity = 150  # defined depending on the arm's size

        self.precision = precision

        super().__init__(shelf_size_x, shelf_size_y, precision)

    def __getSucessors(self, currentNode):
        """ Cette methode permet de generer le graph en fonction des objets dans l'espace

        Un noeud ne peut avoir qu'un fils par contre il peut avoir plusieurs parents.
        """

        for node in self.__graph:
            if node.name is not currentNode.name:
                if not self.__isCollide(currentNode, node):
                    new_node = cp.deepcopy(node)
                    new_node.resetChild()

                    currentNode.setChild(new_node)
                    new_node.setParent(currentNode)

        return currentNode.getChild()

    def defineObjectToMove(self, robotArm, algo_name, occurence_test=True):
        """Cette methode definit la liste des objets a bouger pour atteindre l'object goal.
            En verifiant auparavant si l'objet goal ne peut pas etre atteint directement.
        """

        objectsToMove = []

        solution = None
        nb_iterations = 0

        if algo_name == "BFS":
            solution, nb_iterations = self.breath_first_search(
                robotArm, occurence_test=occurence_test)
        elif algo_name == "DFS":
            solution, nb_iterations = self.depth_first_search(
                robotArm, occurence_test=occurence_test)

        if solution:
            print("Solver : Solution found")

        objectsToMove.append(solution)
        parent = solution.getParent()

        while parent:
            objectsToMove.append(parent)

            parent = parent.getParent()

        objectsToMove.reverse()

        return objectsToMove, nb_iterations

    def breath_first_search(self, robotArm, occurence_test=True):
        frontier = list()
        explored = []
        frontier.append(robotArm)

        i = 0

        while frontier:
            state = frontier.pop(0)

            if state.isGoal():
                return state, i

            children = self.__getSucessors(state)

            for child in children:
                if not occurence_test or (child.name not in explored):
                    frontier.append(child)
                    if occurence_test:
                        explored.append(child.name)

            i += 1

        return None

    def depth_first_search(self, robotArm, occurence_test=True):
        frontier = list()
        explored = []
        frontier.append(robotArm)

        i = 0

        while frontier:
            state = frontier.pop()

            explored.append(state)

            if state == self.goal:
                return state, i

            children = self.__getSucessors(state)

            for child in children:
                if not occurence_test or (child.name not in explored.name):
                    frontier.insert(0, child)
                    if occurence_test:
                        explored.append(child.name)

                i += 1

        return None

    def __getDistanceToClosestObjectsFromPoint(self, point):
        closest_node = None
        min_dist = 100000

        for obj in self.__graph:
            if(min_dist > (obj.getDistanceTo(point) + obj.size/2)):
                closest_node = obj
                min_dist = obj.getDistanceTo(point) + obj.size/2

        return closest_node, min_dist

    def __isCollide(self, starting_node, ending_node):
        """ This method is based on the Bresenham algorithm

            This algorithm is well known for drawing lines between two points in a grid.

            In our case, we use this algorithm to link two poses with a line and for each cell of this line, we check if the arm can pass without touching any other object.
        Args:
            starting_node (Node or RobotArm):
            ending_node (Node):
        """

        sx, sy, dx, dy = 0, 0, 0, 0

        x, y = starting_node.x, starting_node.y

        if(x < ending_node.x):
            sx = 1
        else:
            sx = -1

        if(y < ending_node.y):
            sy = 1
        else:
            sy = -1

        dx = abs(x - ending_node.x)
        dy = abs(y - ending_node.y)
        e = dx - dy

        while(x != ending_node.x or y != ending_node.y):
            e2 = e * 2

            if e2 > - dy:
                e -= dy
                x += sx

            if e2 < dx:
                e += dx
                y += sy

            if(x != ending_node.x or y != ending_node.y):
                node, distanceToClosestNode = self.__getDistanceToClosestObjectsFromPoint([
                    x, y, 0])

                if node.name is not ending_node.name and node.name is not starting_node.name:
                    if distanceToClosestNode < self.objectRadiusProximity:
                        return True

        return False

    def resetNodesChild(self):
        for node in self.__graph:
            node.resetChild()
            node.resetParent()
