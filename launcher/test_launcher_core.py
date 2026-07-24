"""Tests for launcher command generation; no graphical display is required."""

import unittest

from launcher_core import (
    MODE_MULTI,
    MODE_RL,
    MODE_SEARCH,
    LaunchConfig,
    build_launch_spec,
    difficulty_profile,
)


class LauncherCoreTests(unittest.TestCase):
    def test_hybrid_command(self):
        spec = build_launch_spec(
            LaunchConfig(
                mode=MODE_MULTI,
                algorithm="混合智能体 Hybrid",
                layout="smallClassic",
                ghost="DirectionalGhost",
                ghosts=2,
                depth=2,
                games=3,
                speed=0.05,
                fixed_seed=True,
            ),
            python_executable="/test/python",
        )
        self.assertEqual(spec.cwd.name, "multiagent")
        self.assertEqual(spec.command[0], "/test/python")
        self.assertIn("HybridPacmanAgent", spec.command)
        self.assertIn("depth=2,dangerDepth=3", spec.command)
        self.assertEqual(spec.command[-1], "-f")

    def test_astar_command_has_no_ghosts(self):
        spec = build_launch_spec(
            LaunchConfig(
                mode=MODE_SEARCH,
                algorithm="A* 搜索",
                layout="mediumMaze",
            )
        )
        self.assertEqual(spec.cwd.name, "search")
        self.assertIn(
            "fn=aStarSearch,heuristic=manhattanHeuristic", spec.command
        )
        ghost_count_index = spec.command.index("-k") + 1
        self.assertEqual(spec.command[ghost_count_index], "0")

    def test_reinforcement_total_includes_training_and_display(self):
        spec = build_launch_spec(
            LaunchConfig(
                mode=MODE_RL,
                algorithm="近似 Q-learning",
                layout="smallGrid",
                training=500,
                games=5,
            )
        )
        self.assertEqual(spec.cwd.name, "reinforcement")
        self.assertIn("extractor=SimpleExtractor", spec.command)
        training_index = spec.command.index("-x") + 1
        total_index = spec.command.index("-n") + 1
        self.assertEqual(spec.command[training_index], "500")
        self.assertEqual(spec.command[total_index], "505")

    def test_difficulty_profiles_match_modes(self):
        self.assertEqual(
            difficulty_profile("入门", MODE_SEARCH)["layout"], "tinyMaze"
        )
        self.assertEqual(
            difficulty_profile("困难", MODE_MULTI)["depth"], 3
        )
        self.assertEqual(
            difficulty_profile("挑战", MODE_RL)["training"], 5000
        )

    def test_invalid_layout_is_rejected(self):
        with self.assertRaises(ValueError):
            build_launch_spec(LaunchConfig(
                mode=MODE_SEARCH,
                algorithm="广度优先 BFS",
                layout="not-a-layout",
            ))


if __name__ == "__main__":
    unittest.main()
