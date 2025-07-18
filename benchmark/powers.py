from typing import List, Optional

import torch
import torch.backends.opt_einsum
import torch.nn as nn
import typer

from benchmark.utils import loss_win_condition, trial
from heavyball.utils import set_torch

app = typer.Typer(pretty_exceptions_enable=False)
set_torch()
configs = {
    "trivial": {"powers": 4},
    "easy": {"powers": 8},
    "medium": {"powers": 16},
    "hard": {"powers": 32},
    "extreme": {"powers": 128},
    "nightmare": {"powers": 512},
}


class Model(nn.Module):
    def __init__(self, size, powers, target):
        super().__init__()
        self.target = target
        self.param = nn.Parameter(torch.rand(powers, size) * 2)
        self.register_buffer("scale", torch.arange(powers).float().add(1))

    def forward(self):
        x = self.param - self.target
        x = x ** self.scale.view(-1, 1)
        return x.square().mean()


@app.command()
def main(
    method: List[str] = typer.Option(["qr"], help="Eigenvector method to use (for SOAP)"),
    dtype: List[str] = typer.Option(["float32"], help="Data type to use"),
    size: int = 64,
    powers: int = 8,
    steps: int = 10,
    target: float = 1.0,
    weight_decay: float = 0,
    opt: List[str] = typer.Option(["ForeachSOAP"], help="Optimizers to use"),
    win_condition_multiplier: float = 1.0,
    trials: int = 10,
    config: Optional[str] = None,
):
    powers = configs.get(config, {}).get("powers", powers)
    model = Model(size, powers, target).cuda().double()

    trial(
        model,
        None,
        None,
        loss_win_condition(win_condition_multiplier * 1e-8),
        steps,
        opt[0],
        weight_decay,
        failure_threshold=3,
        trials=trials,
    )


if __name__ == "__main__":
    app()
