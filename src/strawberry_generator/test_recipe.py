import unittest
from strawberry_generator.recipe import Recipe
class RecipeTests(unittest.TestCase):
    def test_two_independent_seeds(self):
        a=Recipe(101,264,.23,-.12,1.08);b=Recipe(202,264,-.12,.18,.96)
        self.assertNotEqual(a.seed,b.seed);self.assertEqual(a,Recipe(101,264,.23,-.12,1.08))
    def test_unsupported_count_is_explicit(self):
        for count in [240,280,True,264.0]:
            with self.assertRaises(ValueError):Recipe(101,count,0,0,1)
    def test_invalid_seed(self):
        for seed in [True,-1,2**31,'101']:
            with self.assertRaises(ValueError):Recipe(seed,264,0,0,1)
    def test_invalid_profile(self):
        for a,b,h in [(float('nan'),0,1),(0,float('inf'),1),(0,0,0),(.31,0,1),(0,-.26,1),(False,0,1)]:
            with self.assertRaises(ValueError):Recipe(101,264,a,b,h)
if __name__=='__main__':unittest.main()
