import unittest

from imageProcessing.GibTopologizer import orderGibsByZCoordinates
from unitTests.TestUtilities import initializeLoggingForTest


class GibTopologyTest(unittest.TestCase):
    def setUp(self) -> None:
        initializeLoggingForTest(self)

    # TODO: RESUME HERE: maybe not sufficient? also check seam values?
    def test_orderGibsByZCoordinates(self):
        # ARRANGE
        oldGibs = []

        gib1 = {}
        oldGibs.append(gib1)
        gib1['id'] = 1
        gib1['z'] = 2
        gib1['coversNeighbour'] = {}
        gib1['coveredByNeighbour'] = {}
        gib1['neighbourToSeam'] = {}

        gib2 = {}
        oldGibs.append(gib2)
        gib2['id'] = 2
        gib2['z'] = 1
        gib2['coversNeighbour'] = {}
        gib2['coveredByNeighbour'] = {}
        gib2['neighbourToSeam'] = {}

        gib3 = {}
        oldGibs.append(gib3)
        gib3['id'] = 3
        gib3['z'] = 3
        gib3['coversNeighbour'] = {}
        gib3['coveredByNeighbour'] = {}
        gib3['neighbourToSeam'] = {}

        gib1['coversNeighbour'][1] = False
        gib1['coversNeighbour'][2] = True
        gib1['coversNeighbour'][3] = False
        gib1['coveredByNeighbour'][1] = False
        gib1['coveredByNeighbour'][2] = False
        gib1['coveredByNeighbour'][3] = True
        gib1['neighbourToSeam'][1] = []
        gib1['neighbourToSeam'][2] = [(1, 2)]
        gib1['neighbourToSeam'][3] = [(1, 3)]

        gib2['coversNeighbour'][1] = False
        gib2['coversNeighbour'][2] = False
        gib2['coversNeighbour'][3] = False
        gib2['coveredByNeighbour'][1] = True
        gib2['coveredByNeighbour'][2] = False
        gib2['coveredByNeighbour'][3] = True
        gib2['neighbourToSeam'][1] = []
        gib2['neighbourToSeam'][2] = []
        gib2['neighbourToSeam'][3] = [(2, 3)]

        gib3['coversNeighbour'][1] = True
        gib3['coversNeighbour'][2] = True
        gib3['coversNeighbour'][3] = False
        gib3['coveredByNeighbour'][1] = False
        gib3['coveredByNeighbour'][2] = False
        gib3['coveredByNeighbour'][3] = False
        gib3['neighbourToSeam'][1] = [(3, 1)]
        gib3['neighbourToSeam'][2] = [(3, 2)]
        gib3['neighbourToSeam'][3] = []

        # ACT
        newGibs = orderGibsByZCoordinates(oldGibs)

        # ASSERT
        # gib3 -> 1, gib1 -> 2, gib2 -> 3
        self.assertTrue(newGibs[0]['id'] == 1)  # former gib3
        self.assertTrue(newGibs[0]['z'] == 3)
        self.assertTrue(newGibs[0]['coversNeighbour'][1] == False)
        self.assertTrue(newGibs[0]['coversNeighbour'][2] == True)
        self.assertTrue(newGibs[0]['coversNeighbour'][3] == True)
        self.assertTrue(newGibs[0]['coveredByNeighbour'][1] == False)
        self.assertTrue(newGibs[0]['coveredByNeighbour'][2] == False)
        self.assertTrue(newGibs[0]['coveredByNeighbour'][3] == False)
        self.assertTrue(newGibs[0]['neighbourToSeam'][1] == [])
        self.assertTrue(newGibs[0]['neighbourToSeam'][2] == [(3, 1)])
        self.assertTrue(newGibs[0]['neighbourToSeam'][3] == [(3, 2)])

        self.assertTrue(newGibs[1]['id'] == 2)  # former gib1
        self.assertTrue(newGibs[1]['z'] == 2)
        self.assertTrue(newGibs[1]['coversNeighbour'][1] == False)
        self.assertTrue(newGibs[1]['coversNeighbour'][2] == False)
        self.assertTrue(newGibs[1]['coversNeighbour'][3] == True)
        self.assertTrue(newGibs[1]['coveredByNeighbour'][1] == True)
        self.assertTrue(newGibs[1]['coveredByNeighbour'][2] == False)
        self.assertTrue(newGibs[1]['coveredByNeighbour'][3] == False)
        self.assertTrue(newGibs[1]['neighbourToSeam'][1] == [(1, 3)])
        self.assertTrue(newGibs[1]['neighbourToSeam'][2] == [])
        self.assertTrue(newGibs[1]['neighbourToSeam'][3] == [(1, 2)])

        self.assertTrue(newGibs[2]['id'] == 3)  # former gib2
        self.assertTrue(newGibs[2]['z'] == 1)
        self.assertTrue(newGibs[2]['coversNeighbour'][1] == False)
        self.assertTrue(newGibs[2]['coversNeighbour'][2] == False)
        self.assertTrue(newGibs[2]['coversNeighbour'][3] == False)
        self.assertTrue(newGibs[2]['coveredByNeighbour'][1] == True)
        self.assertTrue(newGibs[2]['coveredByNeighbour'][2] == True)
        self.assertTrue(newGibs[2]['coveredByNeighbour'][3] == False)
        self.assertTrue(newGibs[2]['neighbourToSeam'][1] == [(2, 3)])
        self.assertTrue(newGibs[2]['neighbourToSeam'][2] == [])
        self.assertTrue(newGibs[2]['neighbourToSeam'][3] == [])


if __name__ == '__main__':
    unittest.main()
