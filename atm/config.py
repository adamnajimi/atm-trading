"""Chargement et validation de la configuration.

Les plafonds ci-dessous sont les contraintes d'Adam. Le système refuse toute
configuration qui les relâche : il ne peut donc pas « augmenter ses limites ».
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

# Plafonds non négociables (cahier des charges, 2026-11-27).
CEILING_INITIAL_CAPITAL_EUR = 20.0
CEILING_HARD_LOSS_EUR = 10.0


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class RiskConfig:
    initial_eur: float
    hard_loss_limit_eur: float
    operational_loss_limit_eur: float
    max_loss_per_trade_eur: float
    max_daily_loss_eur: float
    gap_safety_factor: float
    max_position_weight: float
    max_data_age_hours: float
    leverage_allowed: bool


@dataclass(frozen=True)
class VenueConfig:
    name: str
    min_order_eur: float
    maker_fee: float
    taker_fee: float
    slippage: float

    @property
    def one_way_cost(self) -> float:
        """Coût d'un ordre au marché (taker + slippage), en fraction du notionnel."""
        return self.taker_fee + self.slippage

    @property
    def round_trip_cost(self) -> float:
        return 2 * self.one_way_cost


@dataclass(frozen=True)
class Config:
    risk: RiskConfig
    venue: VenueConfig
    mode: str
    live_trading_enabled: bool
    universe: tuple[str, ...]
    paper_universe: tuple[str, ...] = ()
    strategies: dict[str, Any] = field(default_factory=dict)
    shadow_strategies: dict[str, Any] = field(default_factory=dict)


def _validate(cfg: Config) -> None:
    r = cfg.risk
    if r.initial_eur > CEILING_INITIAL_CAPITAL_EUR:
        raise ConfigError("capital initial supérieur au plafond autorisé")
    if r.hard_loss_limit_eur > CEILING_HARD_LOSS_EUR:
        raise ConfigError("limite de perte supérieure à 10 € : interdit")
    if not 0 < r.operational_loss_limit_eur < r.hard_loss_limit_eur:
        raise ConfigError("la limite opérationnelle doit être strictement inférieure à la limite dure")
    if r.max_loss_per_trade_eur <= 0 or r.max_loss_per_trade_eur > r.operational_loss_limit_eur:
        raise ConfigError("perte max par trade invalide")
    if r.max_daily_loss_eur <= 0 or r.max_daily_loss_eur > r.operational_loss_limit_eur:
        raise ConfigError("perte max journalière invalide")
    if r.gap_safety_factor < 1.0:
        raise ConfigError("le facteur de sécurité gap doit être >= 1")
    if not 0 < r.max_position_weight <= 1.0:
        raise ConfigError("poids de position > 1 = levier : interdit")
    if r.leverage_allowed:
        raise ConfigError("levier activé sans validation explicite d'Adam : interdit")
    if cfg.mode not in ("paper", "live"):
        raise ConfigError("mode inconnu")
    v = cfg.venue
    if v.min_order_eur <= 0 or v.taker_fee < 0 or v.maker_fee < 0 or v.slippage < 0:
        raise ConfigError("paramètres de plateforme invalides")


def from_dict(d: dict[str, Any]) -> Config:
    try:
        cap, risk, venue, exe = d["capital"], d["risk"], d["venue"], d["execution"]
        cfg = Config(
            risk=RiskConfig(
                initial_eur=float(cap["initial_eur"]),
                hard_loss_limit_eur=float(cap["hard_loss_limit_eur"]),
                operational_loss_limit_eur=float(cap["operational_loss_limit_eur"]),
                max_loss_per_trade_eur=float(risk["max_loss_per_trade_eur"]),
                max_daily_loss_eur=float(risk["max_daily_loss_eur"]),
                gap_safety_factor=float(risk["gap_safety_factor"]),
                max_position_weight=float(risk["max_position_weight"]),
                max_data_age_hours=float(risk["max_data_age_hours"]),
                leverage_allowed=bool(risk["leverage_allowed"]),
            ),
            venue=VenueConfig(
                name=str(venue["name"]),
                min_order_eur=float(venue["min_order_eur"]),
                maker_fee=float(venue["maker_fee"]),
                taker_fee=float(venue["taker_fee"]),
                slippage=float(venue["slippage"]),
            ),
            mode=str(exe["mode"]),
            live_trading_enabled=bool(exe["live_trading_enabled"]),
            universe=tuple(d.get("universe", [])),
            paper_universe=tuple(d.get("paper_universe", d.get("universe", []))),
            strategies=dict(d.get("strategies", {})),
            shadow_strategies=dict(d.get("shadow_strategies", {})),
        )
    except KeyError as e:  # pragma: no cover - message explicite
        raise ConfigError(f"clé de configuration manquante : {e}") from e
    _validate(cfg)
    return cfg


def load(path: str | Path = "config/config.yaml") -> Config:
    with open(path, encoding="utf-8") as f:
        return from_dict(yaml.safe_load(f))


# Essais de limites (autorisés par Adam le 2026-11-27 pour les tests uniquement).
# La perte totale (10 €) et l'arrêt opérationnel (7 €) ne sont jamais modifiables ici.
TRIAL_BOUNDS = {
    "max_loss_per_trade_eur": (0.25, 2.0),
    "max_daily_loss_eur": (0.5, 3.0),
    "gap_safety_factor": (1.25, 3.0),
}


def with_risk_trial(cfg: Config, overrides: dict[str, float] | None) -> Config:
    """Copie de la config avec des limites d'essai bornées. Refuse toute autre clé."""
    if not overrides:
        return cfg
    for k, v in overrides.items():
        if k not in TRIAL_BOUNDS:
            raise ConfigError(f"limite non modifiable en essai : {k}")
        lo, hi = TRIAL_BOUNDS[k]
        if not lo <= float(v) <= hi:
            raise ConfigError(f"{k}={v} hors des bornes d'essai [{lo}, {hi}]")
    trial = replace(cfg, risk=replace(cfg.risk, **{k: float(v) for k, v in overrides.items()}))
    _validate(trial)
    return trial


# Portefeuilles fantômes (fictifs, jamais réels) : réglages autorisés par Adam le 2026-11-28
# (« fais ce qui te semble le mieux ») pour comparer une autre plateforme et un capital de 50 €.
# Ne s'appliquent JAMAIS au portefeuille principal ni à l'argent réel.
SHADOW_BOUNDS = {
    "initial_eur": (5.0, 50.0),
    "hard_loss_limit_eur": (1.0, 15.0),
    "operational_loss_limit_eur": (1.0, 12.0),
    "max_loss_per_trade_eur": (0.25, 1.5),
    "max_daily_loss_eur": (0.5, 3.0),
}
SHADOW_VENUES = {  # tarifs officiels relevés le 2026-11-28 (palier le plus bas, spot EUR)
    "kraken": {"name": "kraken", "min_order_eur": 5.0, "maker_fee": 0.0040, "taker_fee": 0.0080},
    "bitvavo": {"name": "bitvavo", "min_order_eur": 5.0, "maker_fee": 0.0015, "taker_fee": 0.0025},
}


def with_shadow_overrides(cfg: Config, spec: dict) -> Config:
    """Config d'un portefeuille fantôme : essai de limites (bornes d'essai), puis capital/plateforme
    fantômes bornés. Le glissement supposé n'est jamais réduit."""
    out = with_risk_trial(cfg, spec.get("risk_trial"))
    cap = spec.get("shadow_capital") or {}
    for k, v in cap.items():
        if k not in SHADOW_BOUNDS:
            raise ConfigError(f"réglage fantôme non autorisé : {k}")
        lo, hi = SHADOW_BOUNDS[k]
        if not lo <= float(v) <= hi:
            raise ConfigError(f"{k}={v} hors des bornes fantômes [{lo}, {hi}]")
    if cap:
        r = replace(out.risk, **{k: float(v) for k, v in cap.items()})
        if not 0 < r.operational_loss_limit_eur < r.hard_loss_limit_eur:
            raise ConfigError("fantôme : arrêt opérationnel doit être < perte max")
        if r.max_loss_per_trade_eur > r.operational_loss_limit_eur or r.max_daily_loss_eur > r.operational_loss_limit_eur:
            raise ConfigError("fantôme : limites par trade/jour incohérentes")
        out = replace(out, risk=r)
    venue = spec.get("venue")
    if venue:
        if venue not in SHADOW_VENUES:
            raise ConfigError(f"plateforme fantôme inconnue : {venue}")
        out = replace(out, venue=replace(out.venue, **SHADOW_VENUES[venue]))
    return out
