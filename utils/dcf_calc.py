"""
Discounted Cash Flow engine with Monte Carlo and diagnostics
Five year forecast plus terminal value

Built this after reading too many equity research reports that didn't show their work.
The Monte Carlo stuff helps capture the reality that growth rates aren't point estimates.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import warnings

# Suppress numpy warnings - they're annoying and not helpful for this use case
warnings.filterwarnings("ignore")


@dataclass
class CapitalBridge:
    # This gets messy fast - every company has different adjustments
    net_debt: float = 0.0              # debt minus cash
    non_operating_assets: float = 0.0  # equity investments, excess cash
    minority_interest: float = 0.0     # subtract minority interest
    other_adjustments: float = 0.0     # pension deficit etc


class DCFCalculator:
    def __init__(self,
                 risk_free_rate: float = 0.045,
                 market_risk_premium: float = 0.06,
                 default_beta: float = 1.0,
                 seed: Optional[int] = None):
        # Default rates are roughly where we are today (2024)
        self.risk_free_rate = float(risk_free_rate)
        self.market_risk_premium = float(market_risk_premium)
        self.default_beta = float(default_beta)
        # Seed for reproducible Monte Carlo - useful for debugging
        if seed is not None:
            np.random.seed(seed)

    # --------------------------- public api ---------------------------------

    def calculate_dcf_valuation(self,
                                fcf_history: List[float],
                                fcf_growth_rate: float,
                                wacc: float = 0.10,
                                terminal_growth: float = 0.025,
                                shares_outstanding: float = 1e9,
                                monte_carlo_runs: int = 1000,
                                years: int = 5,
                                bridge: Optional[CapitalBridge] = None,
                                annual_share_change: float = 0.0,
                                treat_sbc_as_cash_cost: bool = True,
                                sbc_percent_of_fcf: float = 0.0,
                                real_mode: bool = False,
                                inflation: float = 0.03,
                                recession_prob: float = 0.15) -> Dict:
        """
        Main entry point
        fcf_history: list of historical free cash flows, last element is most recent
        fcf_growth_rate: base nominal growth if real_mode is False, real growth if real_mode is True
        wacc: nominal if real_mode is False, real if real_mode is True
        annual_share_change: positive for dilution, negative for buybacks
        """
        # validate and normalize
        self._validate_inputs(wacc, terminal_growth, years)
        base_fcf = self._pick_base_fcf(fcf_history)
        # Adjust for SBC if treating it as a cash cost (some companies do this)
        if treat_sbc_as_cash_cost and sbc_percent_of_fcf > 0:
            base_fcf = base_fcf * (1.0 - float(sbc_percent_of_fcf))

        # convert to nominal if user chose real mode
        # Most people think in nominal terms anyway, but real mode is cleaner for long-term models
        if real_mode:
            g_nom = (1 + fcf_growth_rate) * (1 + inflation) - 1
            wacc_nom = (1 + wacc) * (1 + inflation) - 1
            tg_nom = (1 + terminal_growth) * (1 + inflation) - 1
        else:
            g_nom, wacc_nom, tg_nom = fcf_growth_rate, wacc, terminal_growth

        bridge = bridge or CapitalBridge()  # Default to no adjustments

        # base case
        base_breakdown = self._base_case_breakdown(
            base_fcf, g_nom, wacc_nom, tg_nom, years,
            shares_outstanding, annual_share_change, bridge
        )

        # monte carlo
        mc_vals, mc_details = self._monte_carlo_vectorized(
            base_fcf=base_fcf,
            base_growth=g_nom,
            base_wacc=wacc_nom,
            base_tg=tg_nom,
            years=years,
            shares=shares_outstanding,
            annual_share_change=annual_share_change,
            bridge=bridge,
            n=monte_carlo_runs,
            recession_prob=recession_prob
        )

        results = {
            "base_case": base_breakdown,
            "monte_carlo": self._summarize_mc(mc_vals),
            "diagnostics": self._diagnostics(base_breakdown, wacc_nom, tg_nom, years),
            "assumptions": {
                "base_fcf": base_fcf,
                "growth_rate": g_nom,
                "wacc": wacc_nom,
                "terminal_growth": tg_nom,
                "years": years,
                "shares_outstanding_start": shares_outstanding,
                "annual_share_change": annual_share_change,
                "treat_sbc_as_cash_cost": treat_sbc_as_cash_cost,
                "sbc_percent_of_fcf": sbc_percent_of_fcf,
                "real_mode": real_mode,
                "inflation": inflation,
                "recession_prob": recession_prob
            },
            "mc_sample_scenarios": mc_details[:10]
        }
        return results

    def calculate_wacc(self,
                       beta: float = 1.0,
                       risk_free_rate: Optional[float] = None,
                       market_risk_premium: Optional[float] = None,
                       cost_of_debt: float = 0.05,
                       tax_rate: float = 0.25,
                       debt_to_equity: float = 0.3) -> float:
        rf = float(
            risk_free_rate if risk_free_rate is not None else self.risk_free_rate)
        mrp = float(
            market_risk_premium if market_risk_premium is not None else self.market_risk_premium)
        coe = rf + float(beta) * mrp
        after_tax_cod = float(cost_of_debt) * (1.0 - float(tax_rate))
        total = 1.0 + float(debt_to_equity)
        w_e = 1.0 / total
        w_d = float(debt_to_equity) / total
        return w_e * coe + w_d * after_tax_cod

    def calculate_valuation_metrics(self,
                                    current_price: float,
                                    dcf_price: float,
                                    market_cap: float,
                                    fcf_history: List[float]) -> Dict:
        if not fcf_history:
            return {}
        current_fcf = self._pick_base_fcf(fcf_history)
        return {
            "dcf_vs_current": (dcf_price - current_price) / current_price,
            "upside_downside_multiple": dcf_price / current_price,
            "fcf_yield": current_fcf / market_cap if market_cap > 0 else 0.0,
            "price_to_fcf": current_price / (current_fcf / 1e9) if current_fcf > 0 else 0.0,
        }

    # --------------------------- internals ----------------------------------

    def _validate_inputs(self, wacc: float, tg: float, years: int):
        # Basic sanity checks
        if years < 3 or years > 10:
            raise ValueError("years must be between 3 and 10")
        if wacc <= tg:
            raise ValueError(
                "WACC must be strictly greater than terminal growth")
        if wacc < 0.0 or tg < 0.0:
            raise ValueError("WACC and terminal growth must be non negative")

    def _pick_base_fcf(self, fcf_history: List[float]) -> float:
        if not fcf_history:
            return 1_000_000_000.0  # $1B default for companies with no FCF data
        # assume last element is most recent
        most_recent = float(fcf_history[-1])
        if most_recent > 0:
            return most_recent
        # fall back to the maximum positive FCF if the most recent is negative
        # This happens with cyclical companies or those with one-off charges
        positives = [x for x in fcf_history if x > 0]
        return float(max(positives)) if positives else 1_000_000_000.0

    def _project_fcf(self, base_fcf: float, g: float, years: int) -> np.ndarray:
        t = np.arange(1, years + 1, dtype=float)
        return float(base_fcf) * np.power(1.0 + float(g), t)

    def _pv_series(self, cashflows: np.ndarray, rate: float) -> np.ndarray:
        t = np.arange(1, cashflows.size + 1, dtype=float)
        return cashflows / np.power(1.0 + float(rate), t)

    def _terminal_value(self, last_fcf: float, wacc: float, tg: float) -> float:
        if wacc <= tg:
            tg = min(tg, wacc - 1e-6)
        return float(last_fcf) * (1.0 + float(tg)) / (float(wacc) - float(tg))

    def _shares_path(self, start_shares: float, annual_change: float, years: int) -> float:
        return float(start_shares) * np.power(1.0 + float(annual_change), years)

    def _base_case_breakdown(self,
                             base_fcf: float,
                             g: float,
                             wacc: float,
                             tg: float,
                             years: int,
                             shares_out: float,
                             annual_share_change: float,
                             bridge: CapitalBridge) -> Dict:
        fcf = self._project_fcf(base_fcf, g, years)
        pv_explicit = self._pv_series(fcf, wacc)
        terminal_fcf = fcf[-1]
        tv = self._terminal_value(terminal_fcf, wacc, tg)
        pv_tv = tv / np.power(1.0 + wacc, years)

        ev = float(pv_explicit.sum() + pv_tv)

        equity_value = ev \
            - float(bridge.net_debt) \
            + float(bridge.non_operating_assets) \
            - float(bridge.minority_interest) \
            + float(bridge.other_adjustments)

        end_shares = self._shares_path(shares_out, annual_share_change, years)
        per_share = equity_value / end_shares if end_shares > 0 else np.nan

        return {
            "enterprise_value": ev,
            "equity_value": equity_value,
            "equity_value_per_share": per_share,
            "pv_explicit_period": float(pv_explicit.sum()),
            "pv_terminal_value": float(pv_tv),
            "terminal_value_gordon": float(tv),
            "terminal_value_share_of_ev": float(pv_tv / ev) if ev > 0 else np.nan,
            "fcf_projections": fcf.tolist(),
            "pv_fcf_projections": pv_explicit.tolist(),
            "terminal_fcf_year": float(terminal_fcf),
            "shares_end_year": float(end_shares),
        }

    # Monte Carlo with fat tails and a simple recession regime
    # The fat tails are important - markets have more extreme moves than normal distributions suggest
    def _monte_carlo_vectorized(self,
                                base_fcf: float,
                                base_growth: float,
                                base_wacc: float,
                                base_tg: float,
                                years: int,
                                shares: float,
                                annual_share_change: float,
                                bridge: CapitalBridge,
                                n: int,
                                recession_prob: float) -> Tuple[np.ndarray, List[Dict]]:
        n = int(n)

        # regime flag - simple way to model different economic environments
        recession = np.random.rand(n) < float(recession_prob)

        # growth distribution: normal core with student t fat tails
        # The t-distribution captures the reality that growth rates have fatter tails than normal
        core_g = np.random.normal(loc=base_growth, scale=0.02, size=n)
        tail_g = base_growth + 0.04 * np.random.standard_t(df=5, size=n)
        g = np.where(recession, np.minimum(
            core_g, base_growth - 0.03), 0.7 * core_g + 0.3 * tail_g)
        g = np.clip(g, -0.30, 0.40)  # Reasonable bounds for corporate growth

        # wacc distribution: normal with floor and cap
        # WACC is usually more stable than growth, but still has uncertainty
        core_w = np.random.normal(loc=base_wacc, scale=0.01, size=n)
        tail_w = base_wacc + 0.02 * np.random.standard_t(df=6, size=n)
        w = 0.7 * core_w + 0.3 * tail_w
        # Risk-free rate usually goes up in recessions
        w = np.where(recession, w + 0.01, w)
        w = np.clip(w, 0.05, 0.20)  # Reasonable WACC bounds

        # terminal growth distribution: tight and below wacc
        # Terminal growth should be close to long-term GDP growth (2-3%)
        tg = np.random.normal(loc=base_tg, scale=0.003, size=n)
        tg = np.clip(tg, 0.005, 0.04)
        tg = np.minimum(tg, w - 1e-4)  # Always ensure WACC > terminal growth

        # base fcf randomization: lognormal noise around base with harsher recession cut
        # Lognormal ensures FCF stays positive and captures the multiplicative nature of business
        sigma = 0.10
        base_draw = base_fcf * \
            np.exp(np.random.normal(loc=0.0, scale=np.log(1 + sigma), size=n))
        base_draw = np.where(recession, base_draw * 0.9,
                             base_draw)  # 10% cut in recessions

        # vectorized valuation - this is where numpy really shines
        t = np.arange(1, years + 1, dtype=float)
        growth_matrix = np.power(1.0 + g[:, None], t[None, :])
        fcf_paths = base_draw[:, None] * growth_matrix

        disc_matrix = np.power(1.0 + w[:, None], t[None, :])
        pv_explicit = (fcf_paths / disc_matrix).sum(axis=1)

        terminal_fcf = fcf_paths[:, -1]
        tv = (terminal_fcf * (1.0 + tg)) / (w - tg)
        pv_tv = tv / np.power(1.0 + w, years)

        ev = pv_explicit + pv_tv

        equity = ev \
            - float(bridge.net_debt) \
            + float(bridge.non_operating_assets) \
            - float(bridge.minority_interest) \
            + float(bridge.other_adjustments)

        end_shares = self._shares_path(shares, annual_share_change, years)
        per_share = equity / end_shares if end_shares > 0 else np.nan

        # small sample of scenario details for transparency
        # Helps users understand what drove the valuation range
        details = []
        take = min(25, n)
        idx = np.random.choice(np.arange(n), size=take, replace=False)
        for i in idx:
            details.append({
                "base_fcf": float(base_draw[i]),
                "growth_rate": float(g[i]),
                "wacc": float(w[i]),
                "terminal_growth": float(tg[i]),
                "enterprise_value": float(ev[i]),
                "equity_value_per_share": float(per_share[i]),
                "recession": bool(recession[i]),
            })

        return per_share, details

    def _summarize_mc(self, per_share: np.ndarray) -> Dict:
        if per_share.size == 0 or not np.isfinite(per_share).any():
            return {
                "mean": np.nan, "median": np.nan, "std": np.nan,
                "p5": np.nan, "p25": np.nan, "p75": np.nan, "p95": np.nan,
                "min": np.nan, "max": np.nan, "count": 0
            }
        clean = per_share[np.isfinite(per_share)]
        return {
            "mean": float(np.mean(clean)),
            "median": float(np.median(clean)),
            "std": float(np.std(clean)),
            "p5": float(np.percentile(clean, 5)),
            "p25": float(np.percentile(clean, 25)),
            "p75": float(np.percentile(clean, 75)),
            "p95": float(np.percentile(clean, 95)),
            "min": float(np.min(clean)),
            "max": float(np.max(clean)),
            "count": int(clean.size)
        }

    def _diagnostics(self, base: Dict, wacc: float, tg: float, years: int) -> Dict:
        """
        Provide model health checks and useful context
        These flags help catch common DCF modeling mistakes
        """
        ev = float(base.get("enterprise_value", np.nan))
        pv_exp = float(base.get("pv_explicit_period", np.nan))
        pv_tv = float(base.get("pv_terminal_value", np.nan))
        fcf_pv = np.array(base.get("pv_fcf_projections", []), dtype=float)

        # terminal share and flag
        # If >70% of value comes from terminal value, the model is very sensitive to assumptions
        terminal_share = float(pv_tv / ev) if ev > 0 else np.nan
        terminal_dominant = bool(terminal_share > 0.7) if np.isfinite(
            terminal_share) else False

        # value duration like Macaulay duration on PV cash flows
        # Shows how much of the value comes from near-term vs long-term cash flows
        if fcf_pv.size > 0 and np.isfinite(fcf_pv).all():
            t = np.arange(1, fcf_pv.size + 1, dtype=float)
            weights = fcf_pv / \
                np.sum(fcf_pv) if np.sum(fcf_pv) > 0 else np.zeros_like(fcf_pv)
            duration_years = float(np.sum(t * weights))
        else:
            duration_years = np.nan

        # sanity flags - common issues that make DCF models unreliable
        flags = []
        if wacc <= tg:
            flags.append("WACC not greater than terminal growth")
        if not np.isfinite(ev) or ev <= 0:
            flags.append("Enterprise value non positive")
        if duration_years and duration_years < 2.0:
            flags.append("Short duration implies heavy back loading")
        if terminal_dominant:
            flags.append("Terminal value dominates the enterprise value")

        return {
            "terminal_value_share": terminal_share,
            "terminal_value_dominant": terminal_dominant,
            "duration_years_pv_cashflows": duration_years,
            "pv_explicit_to_pv_terminal_ratio": float(pv_exp / pv_tv) if pv_tv > 0 else np.nan,
            "health_flags": flags
        }
