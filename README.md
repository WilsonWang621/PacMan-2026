# AIPacMan-2026：Pacman AI 综合项目

本项目基于 UC Berkeley CS 188 的 Pacman AI 教学框架，完整覆盖经典搜索、
多智能体博弈、命题逻辑、概率追踪、机器学习和强化学习，并额外实现了：

- `HybridPacmanAgent`：融合迷宫距离、期望搜索和风险搜索的混合智能体；
- Pacman AI Arena：中文桌面图形化启动器；
- 固定种子的智能体性能对照工具；
- 适用于回归、分类、语言识别、卷积网络和深度 Q 网络的 PyTorch 模型。

> 原项目与框架归 UC Berkeley CS 188 团队所有。本仓库仅用于课程学习和
> 教学实践，请遵守各源文件中的许可与署名要求。

## 1. 仓库结构

```text
PacMan/
├── launcher/           中文图形化启动器、启动配置和前端测试
├── tutorial/           Python 基础练习
├── search/             DFS、BFS、UCS、A* 与食物/角落搜索
├── multiagent/         Reflex、Minimax、Alpha-Beta、Expectimax、Hybrid
├── logic/              命题逻辑、SAT 与逻辑规划
├── tracking/           贝叶斯网络、HMM 与幽灵位置推断
├── machinelearning/    回归、数字分类、语言识别、卷积模型
├── reinforcement/      Value Iteration、Q-learning、Approximate Q、DQN
├── docs/               各核心算法的补充说明
├── requirements.txt    完整项目的 Python 依赖
└── README.md           项目总览、安装、运行与测试手册
```

每个课程模块保留自己的 `README.md`、`autograder.py`、`test_cases/` 和
Pacman 基础框架。为了避免破坏课程测试，各模块仍可独立进入目录运行。

## 2. 环境要求

推荐环境：

- Linux、WSL2、macOS 或 Windows；
- Python 3.11；Python 3.9 也可用于原版课程框架；
- Tk 图形库；
- NumPy、Matplotlib、PycoSAT 和 PyTorch；
- 图形化环境需要可用桌面显示；纯测试可以使用 `--no-graphics`。

当前开发环境验证过：

```text
Python       3.11
NumPy        2.4.4
Matplotlib   3.11.1
PyTorch      2.13.0+cpu
```

PyTorch 版本不必与上面完全一致。CPU 版本可以运行全部项目；GPU 主要加速
机器学习和深度强化学习训练，不会明显加速 Minimax、Expectimax 或 Hybrid
这类 Python 搜索算法。

## 3. 安装手册

### 3.1 使用 Conda 创建环境

```bash
git clone https://github.com/WilsonWang621/PacMan-2026.git
cd PacMan-2026

conda create -n pacman python=3.11 -y
conda activate pacman
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

如果环境已经存在：

```bash
cd PacMan-2026
conda activate pacman
python -m pip install -r requirements.txt
```

### 3.2 Linux/WSL 图形界面依赖

Ubuntu 或 Debian 可以安装：

```bash
sudo apt update
sudo apt install python3-tk fonts-noto-cjk
```

如果 Conda 自带的 Tk 无法识别中文字体，启动器会在 Linux 上自动使用
`/usr/bin/python3` 的 Tk 绘制界面，同时继续使用 Conda 环境中的 Python
运行 Pacman，因此不会丢失 NumPy、PyTorch 等环境依赖。

WSL 用户还需要 WSLg 或可用的 X Server。可以检查：

```bash
echo "$DISPLAY"
```

输出不为空通常表示图形程序可以打开窗口。

### 3.3 PyTorch CPU/GPU 选择

普通安装：

```bash
python -m pip install torch
```

如果需要 NVIDIA GPU，请根据显卡驱动和 CUDA 版本使用
[PyTorch 官方安装选择器](https://pytorch.org/get-started/locally/)生成命令。
安装后检查：

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

输出 `True` 表示 PyTorch 可以使用 CUDA。

## 4. 图形化启动器

### 4.1 启动

```bash
cd PacMan-2026
conda activate pacman
python launcher/launcher.py
```

也可以不激活环境：

```bash
conda run -n pacman python launcher/launcher.py
```

启动器只负责生成并启动原版 Pacman 命令，不修改各课程模块的基础框架。

### 4.2 游戏模式

| 选项 | 用途 |
|---|---|
| 对抗与混合 | 在有幽灵的经典地图上比较手工评价、博弈搜索和 Hybrid |
| 路径搜索 | 在无幽灵迷宫中观察 DFS、BFS、UCS、A* 等路径规划过程 |
| 强化学习 | 先静默训练 Q-learning 智能体，再显示训练后的测试局 |

### 4.3 难度分级

难度按钮会同时设置推荐地图、幽灵行为、幽灵数量、搜索深度、训练局数和
动画速度。之后仍可手动覆盖任意参数。

| 难度 | 对抗与混合 | 路径搜索 | 强化学习 |
|---|---|---|---|
| 入门 | `smallClassic`、1 个随机幽灵、depth 1 | `tinyMaze` | `smallGrid`、训练 500 局 |
| 标准 | `mediumClassic`、2 个追踪幽灵、depth 2 | `mediumMaze` | `smallGrid`、训练 1500 局 |
| 困难 | `trickyClassic`、2 个追踪幽灵、depth 3 | `bigMaze` | `mediumGrid`、训练 3000 局 |
| 挑战 | `contestClassic`、3 个追踪幽灵、depth 3 | `bigSearch` | `mediumClassic`、训练 5000 局 |

### 4.4 对抗与混合智能体

| 选项 | 用途 |
|---|---|
| 混合智能体 Hybrid | 精确迷宫距离负责导航，期望搜索处理随机性，风险分支防范幽灵 |
| 反射智能体 Reflex | 只评价当前动作的直接后果，速度快，适合作为基线 |
| 极小极大 Minimax | 假设幽灵始终采取对 Pacman 最不利的动作 |
| Alpha-Beta 剪枝 | 与 Minimax 决策等价，但跳过不影响最终结果的分支 |
| 期望极大 Expectimax | 把幽灵行为视为随机分布，通常比 Minimax 更积极 |
| 键盘手动游玩 | 使用方向键或 `W/A/S/D` 手动控制 Pacman |

Hybrid 的参数含义：

- `depth`：常规搜索深度；
- `dangerDepth`：活跃幽灵接近时采用的搜索深度；
- 深度每增加 1，计算量可能增长几十倍；
- 大地图或 3 个幽灵建议使用 `depth=2,dangerDepth=3`；
- `depth=3,dangerDepth=4` 更重视决策质量，但危险时可能短暂停顿。

### 4.5 路径搜索算法

| 选项 | 用途 |
|---|---|
| 深度优先 DFS | 优先探索最深节点，不保证最短路径 |
| 广度优先 BFS | 按层扩展；单位代价地图上可以得到最短路径 |
| 一致代价 UCS | 每次扩展累计代价最低的节点，适合不同边权 |
| A* 搜索 | 使用启发函数引导 UCS，兼顾最优性和搜索效率 |
| A* 角落规划 | 规划经过地图全部四个角落的路线 |
| A* 全食物规划 | 把吃完全部食物作为联合搜索问题 |
| 逐豆搜索 Closest Dot | 重复前往最近食物，速度快但不保证全局最优 |

### 4.6 强化学习算法

| 选项 | 用途 |
|---|---|
| 表格型 Q-learning | 为每个状态—动作对维护独立 Q 值，适合小状态空间 |
| 近似 Q-learning | 使用特征权重近似 Q 值，可以泛化到未见过的状态 |

强化学习界面的“训练局数”表示不显示画面的学习阶段，“展示局数”表示训练
结束后以 `epsilon=0`、`alpha=0` 运行并显示的测试局数。

### 4.7 其他界面选项

| 选项 | 用途 |
|---|---|
| 地图 | 选择迷宫规模和结构；括号内为底层 layout 名称 |
| 幽灵行为 | “随机移动”均匀选择动作；“主动追踪”大概率向 Pacman 靠近 |
| 幽灵数量 | 最多使用地图中存在的幽灵出生位置数量 |
| 搜索深度 | 控制 Minimax、Alpha-Beta、Expectimax 和 Hybrid 的前瞻轮数 |
| 展示局数 | 连续运行多少局；单局胜率只能是 0% 或 100% |
| 训练局数 | 仅强化学习模式生效 |
| 动画间隔 | 每个动作显示后的等待时间，不包括智能体计算时间 |
| 固定随机种子 | 使随机过程可复现，适合公平对照 |
| 命令预览 | 显示前端即将执行的完整命令 |
| 实时运行日志 | 显示得分、胜负、平均分和退出状态 |
| 启动游戏 | 在独立 Pacman 窗口运行所选配置 |
| 终止 | 结束当前启动的 Pacman 进程 |

## 5. 常用命令

### 5.1 Hybrid 图形化对战

```bash
cd multiagent
python pacman.py \
  -p HybridPacmanAgent \
  -l mediumClassic \
  -g DirectionalGhost \
  -k 2 \
  -n 1 \
  -a depth=2,dangerDepth=3
```

### 5.2 A* 路径搜索

```bash
cd search
python pacman.py \
  -l mediumMaze \
  -p SearchAgent \
  -a fn=aStarSearch,heuristic=manhattanHeuristic
```

### 5.3 Alpha-Beta 对战

```bash
cd multiagent
python pacman.py \
  -p AlphaBetaAgent \
  -a depth=3,evalFn=better \
  -l mediumClassic
```

### 5.4 Approximate Q-learning

下面先训练 1500 局，再显示 5 局：

```bash
cd reinforcement
python pacman.py \
  -p ApproximateQAgent \
  -a extractor=SimpleExtractor \
  -x 1500 \
  -n 1505 \
  -l smallGrid
```

### 5.5 Hybrid 性能对照

```bash
cd multiagent
python benchmark_hybrid.py --layout smallClassic --games 20
python benchmark_hybrid.py --layout mediumClassic --games 10
```

基准脚本使用固定种子，对比 Reflex、Alpha-Beta、Expectimax 和 Hybrid 的
平均分与胜局数。

## 6. 测试

### 6.1 单独测试一个模块

```bash
cd search
python autograder.py --no-graphics
```

只运行一个问题：

```bash
python autograder.py -q q3 --no-graphics
```

### 6.2 运行全部课程测试

在仓库根目录执行：

```bash
for module in tutorial search multiagent logic tracking machinelearning reinforcement; do
  echo "========== $module =========="
  (cd "$module" && python autograder.py --no-graphics)
done
```

机器学习测试通常需要数分钟；逻辑规划和深度强化学习也可能明显慢于普通
搜索测试。

### 6.3 前端测试

```bash
cd launcher
python -m unittest -v
python launcher.py --dry-run
```

`--dry-run` 只检查默认配置和生成命令，不打开图形窗口。

## 7. 计分与胜率说明

- 吃普通食物加分；
- 吃能量豆后可以在幽灵受惊期间吃幽灵；
- 每移动一步会扣除时间分；
- 被正常幽灵碰到扣 500 分并判负；
- 只有吃完全部食物才会额外加 500 分并判胜；
- `-n 1` 只运行一局，因此胜率只能显示 `0/1` 或 `1/1`；
- 统计策略稳定性时建议固定种子并运行至少 10 局。

高分但最终显示 `Loss` 表示 Pacman 在吃掉大量食物后被幽灵抓住，并不等于
智能体完全没有效果。

## 8. Git 与生成文件

仓库根目录的 `.gitignore` 会排除：

- `__pycache__/` 和 `*.pyc`；
- 测试覆盖率与工具缓存；
- IDE、操作系统和临时文件；
- 本地训练产生的 `.pt`、`.pth`、`.ckpt` 模型；
- Pacman 运行日志和录制文件。

运行测试后不需要手动提交这些文件。可以用下面的命令确认工作区：

```bash
git status --short
```

## 9. 参考资料

- [UC Berkeley CS 188](https://inst.eecs.berkeley.edu/~cs188/)
- [Berkeley Pacman Projects](https://ai.berkeley.edu/)
- [Artificial Intelligence: A Modern Approach](https://aima.cs.berkeley.edu/)
- [PyTorch 官方文档](https://pytorch.org/docs/stable/index.html)
