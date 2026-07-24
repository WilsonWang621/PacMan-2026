"""Reproducible command-line benchmark for the optional hybrid agent."""

import argparse
import contextlib
import io
import random

import ghostAgents
import layout
import multiAgents
import pacman
import textDisplay

from hybridAgents import HybridPacmanAgent


AGENTS = {
    "Reflex": lambda: multiAgents.ReflexAgent(),
    "AlphaBeta": lambda: multiAgents.AlphaBetaAgent(
        depth="2", evalFn="better"
    ),
    "Expectimax": lambda: multiAgents.ExpectimaxAgent(
        depth="2", evalFn="better"
    ),
    "Hybrid": lambda: HybridPacmanAgent(),
}


def run(agent_factory, layout_name, games, seed):
    random.seed(seed)
    chosen_layout = layout.getLayout(layout_name)
    if chosen_layout is None:
        raise ValueError("Unknown layout: " + layout_name)

    game_list = pacman.runGames(
        layout=chosen_layout,
        pacman=agent_factory(),
        ghosts=[
            ghostAgents.DirectionalGhost(index + 1)
            for index in range(chosen_layout.getNumGhosts())
        ],
        display=textDisplay.NullGraphics(),
        numGames=games,
        record=False,
        catchExceptions=False,
        timeout=30,
    )
    scores = [game.state.getScore() for game in game_list]
    wins = sum(game.state.isWin() for game in game_list)
    return sum(scores) / len(scores), wins


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", default="smallClassic")
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--seed", default="hybrid-benchmark-v1")
    args = parser.parse_args()

    results = {}
    for name, factory in AGENTS.items():
        # Suppress per-game framework output; retain only the comparison table.
        with contextlib.redirect_stdout(io.StringIO()):
            average, wins = run(
                factory, args.layout, args.games, args.seed
            )
        results[name] = (average, wins)

    print("Agent       Average score   Wins")
    print("--------------------------------")
    for name, (average, wins) in results.items():
        print("{:<11} {:>13.2f}   {}/{}".format(
            name, average, wins, args.games
        ))

    strongest_baseline = max(
        results[name][0] for name in ("Reflex", "AlphaBeta", "Expectimax")
    )
    most_baseline_wins = max(
        results[name][1] for name in ("Reflex", "AlphaBeta", "Expectimax")
    )
    if (results["Hybrid"][0] <= strongest_baseline
            or results["Hybrid"][1] < most_baseline_wins):
        raise SystemExit(
            "Hybrid failed the score/win-rate baseline check."
        )
    print("\nPASS: Hybrid beat every baseline by average score without "
          "reducing the best win count.")


if __name__ == "__main__":
    main()
