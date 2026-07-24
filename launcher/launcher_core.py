"""Pure configuration logic for the Pacman AI desktop launcher."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import shlex
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODE_SEARCH = "路径搜索"
MODE_MULTI = "对抗与混合"
MODE_RL = "强化学习"
MODES = (MODE_MULTI, MODE_SEARCH, MODE_RL)


ALGORITHMS: Dict[str, Dict[str, Dict[str, str]]] = {
    MODE_MULTI: {
        "混合智能体 Hybrid": {"agent": "HybridPacmanAgent"},
        "反射智能体 Reflex": {"agent": "ReflexAgent"},
        "极小极大 Minimax": {"agent": "MinimaxAgent"},
        "Alpha-Beta 剪枝": {"agent": "AlphaBetaAgent"},
        "期望极大 Expectimax": {"agent": "ExpectimaxAgent"},
        "键盘手动游玩": {"agent": "KeyboardAgent"},
    },
    MODE_SEARCH: {
        "深度优先 DFS": {
            "agent": "SearchAgent", "args": "fn=depthFirstSearch"
        },
        "广度优先 BFS": {
            "agent": "SearchAgent", "args": "fn=breadthFirstSearch"
        },
        "一致代价 UCS": {
            "agent": "SearchAgent", "args": "fn=uniformCostSearch"
        },
        "A* 搜索": {
            "agent": "SearchAgent",
            "args": "fn=aStarSearch,heuristic=manhattanHeuristic",
        },
        "A* 角落规划": {"agent": "AStarCornersAgent"},
        "A* 全食物规划": {"agent": "AStarFoodSearchAgent"},
        "逐豆搜索 Closest Dot": {"agent": "ClosestDotSearchAgent"},
    },
    MODE_RL: {
        "表格型 Q-learning": {"agent": "PacmanQAgent"},
        "近似 Q-learning": {
            "agent": "ApproximateQAgent",
            "args": "extractor=SimpleExtractor",
        },
    },
}


LAYOUTS = {
    MODE_MULTI: (
        "smallClassic", "mediumClassic", "trickyClassic", "contestClassic",
        "capsuleClassic", "openClassic", "originalClassic", "powerClassic",
    ),
    MODE_SEARCH: (
        "tinyMaze", "smallMaze", "mediumMaze", "bigMaze", "openMaze",
        "tinyCorners", "mediumCorners", "bigCorners", "smallSearch",
        "mediumSearch", "bigSearch", "trickySearch",
    ),
    MODE_RL: (
        "smallGrid", "mediumGrid", "smallClassic", "mediumClassic",
    ),
}


DIFFICULTIES = {
    "入门": {
        MODE_MULTI: {
            "layout": "smallClassic", "ghost": "RandomGhost",
            "ghosts": 1, "depth": 1, "training": 100, "speed": 0.10,
        },
        MODE_SEARCH: {
            "layout": "tinyMaze", "ghost": "RandomGhost",
            "ghosts": 0, "depth": 1, "training": 0, "speed": 0.12,
        },
        MODE_RL: {
            "layout": "smallGrid", "ghost": "RandomGhost",
            "ghosts": 1, "depth": 1, "training": 500, "speed": 0.10,
        },
    },
    "标准": {
        MODE_MULTI: {
            "layout": "mediumClassic", "ghost": "DirectionalGhost",
            "ghosts": 2, "depth": 2, "training": 500, "speed": 0.07,
        },
        MODE_SEARCH: {
            "layout": "mediumMaze", "ghost": "RandomGhost",
            "ghosts": 0, "depth": 1, "training": 0, "speed": 0.07,
        },
        MODE_RL: {
            "layout": "smallGrid", "ghost": "DirectionalGhost",
            "ghosts": 1, "depth": 1, "training": 1500, "speed": 0.07,
        },
    },
    "困难": {
        MODE_MULTI: {
            "layout": "trickyClassic", "ghost": "DirectionalGhost",
            "ghosts": 2, "depth": 3, "training": 1500, "speed": 0.04,
        },
        MODE_SEARCH: {
            "layout": "bigMaze", "ghost": "RandomGhost",
            "ghosts": 0, "depth": 1, "training": 0, "speed": 0.04,
        },
        MODE_RL: {
            "layout": "mediumGrid", "ghost": "DirectionalGhost",
            "ghosts": 2, "depth": 1, "training": 3000, "speed": 0.05,
        },
    },
    "挑战": {
        MODE_MULTI: {
            "layout": "contestClassic", "ghost": "DirectionalGhost",
            "ghosts": 3, "depth": 3, "training": 3000, "speed": 0.025,
        },
        MODE_SEARCH: {
            "layout": "bigSearch", "ghost": "RandomGhost",
            "ghosts": 0, "depth": 1, "training": 0, "speed": 0.025,
        },
        MODE_RL: {
            "layout": "mediumClassic", "ghost": "DirectionalGhost",
            "ghosts": 2, "depth": 1, "training": 5000, "speed": 0.04,
        },
    },
}


@dataclass(frozen=True)
class LaunchConfig:
    mode: str
    algorithm: str
    layout: str
    ghost: str = "DirectionalGhost"
    ghosts: int = 2
    depth: int = 2
    games: int = 1
    training: int = 0
    speed: float = 0.07
    fixed_seed: bool = False


@dataclass(frozen=True)
class LaunchSpec:
    command: List[str]
    cwd: Path
    summary: str

    @property
    def display_command(self) -> str:
        return shlex.join(self.command)


def difficulty_profile(level: str, mode: str) -> Dict[str, object]:
    if level not in DIFFICULTIES:
        raise ValueError("未知难度：" + level)
    if mode not in MODES:
        raise ValueError("未知模式：" + mode)
    return dict(DIFFICULTIES[level][mode])


def algorithms_for(mode: str) -> List[str]:
    if mode not in ALGORITHMS:
        raise ValueError("未知模式：" + mode)
    return list(ALGORITHMS[mode])


def layouts_for(mode: str) -> List[str]:
    if mode not in LAYOUTS:
        raise ValueError("未知模式：" + mode)
    return list(LAYOUTS[mode])


def _validate(config: LaunchConfig) -> None:
    if config.mode not in MODES:
        raise ValueError("未知模式：" + config.mode)
    if config.algorithm not in ALGORITHMS[config.mode]:
        raise ValueError("当前模式不支持该算法：" + config.algorithm)
    if config.layout not in LAYOUTS[config.mode]:
        raise ValueError("当前模式不支持该地图：" + config.layout)
    if config.ghost not in ("RandomGhost", "DirectionalGhost"):
        raise ValueError("未知幽灵类型：" + config.ghost)
    if not 0 <= config.ghosts <= 4:
        raise ValueError("幽灵数量必须在 0 到 4 之间")
    if not 1 <= config.depth <= 5:
        raise ValueError("搜索深度必须在 1 到 5 之间")
    if not 1 <= config.games <= 100:
        raise ValueError("展示局数必须在 1 到 100 之间")
    if not 0 <= config.training <= 100000:
        raise ValueError("训练局数必须在 0 到 100000 之间")
    if not 0 <= config.speed <= 1:
        raise ValueError("动画间隔必须在 0 到 1 秒之间")


def build_launch_spec(
    config: LaunchConfig, python_executable: Optional[str] = None
) -> LaunchSpec:
    """Translate a UI selection into a safe subprocess argument list."""
    _validate(config)
    algorithm = ALGORITHMS[config.mode][config.algorithm]
    executable = python_executable or sys.executable
    module = {
        MODE_SEARCH: "search",
        MODE_MULTI: "multiagent",
        MODE_RL: "reinforcement",
    }[config.mode]
    command = [
        executable, "pacman.py",
        "-p", algorithm["agent"],
        "-l", config.layout,
        "--frameTime", str(config.speed),
    ]

    agent_args = algorithm.get("args", "")
    if config.mode == MODE_MULTI:
        if algorithm["agent"] == "HybridPacmanAgent":
            agent_args = "depth={},dangerDepth={}".format(
                config.depth, min(5, config.depth + 1)
            )
        elif algorithm["agent"] in (
            "MinimaxAgent", "AlphaBetaAgent", "ExpectimaxAgent"
        ):
            agent_args = "depth={},evalFn=better".format(config.depth)
        command.extend([
            "-g", config.ghost, "-k", str(config.ghosts),
            "-n", str(config.games),
        ])
    elif config.mode == MODE_SEARCH:
        command.extend(["-k", "0", "-n", "1"])
    else:
        total_games = config.training + config.games
        command.extend([
            "-g", config.ghost, "-k", str(config.ghosts),
            "-x", str(config.training), "-n", str(total_games),
        ])

    if agent_args:
        command.extend(["-a", agent_args])
    if config.fixed_seed:
        command.append("-f")

    return LaunchSpec(
        command=command,
        cwd=PROJECT_ROOT / module,
        summary="{} · {} · {} · {}局".format(
            config.mode, config.algorithm, config.layout, config.games
        ),
    )
