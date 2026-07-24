# Pacman AI Arena

独立的 Tk 桌面启动器，不修改 Berkeley Pacman 基础框架。

## 启动

```bash
cd /home/wangwenxuan/ACM/PPCA/PacMan
conda run -n pacman python launcher/launcher.py
```

界面支持：

- 路径搜索：DFS、BFS、UCS、A*、角落规划、全食物规划；
- 对抗与混合：Reflex、Minimax、Alpha-Beta、Expectimax、Hybrid，也可键盘手动游玩；
- 强化学习：Q-learning、Approximate Q-learning；
- 入门、标准、困难、挑战四级难度；
- 自定义地图、幽灵类型、数量、搜索深度、训练局数和动画速度；
- 命令预览、运行日志和一键终止。

强化学习首次启动需要先完成所选训练局数，训练过程不会显示图形，
之后才显示测试对局。

## 测试

```bash
cd /home/wangwenxuan/ACM/PPCA/PacMan/launcher
conda run -n pacman python -m unittest -v
conda run -n pacman python launcher.py --dry-run
```
