/**
 * 2×2 Factorial ANOVA — pure TypeScript, no dependencies.
 *
 * Computes:
 *   - Main effect of Style (clinical vs analogy)
 *   - Main effect of Mode   (static  vs dialog)
 *   - Style × Mode interaction
 *
 * Uses the regularized incomplete beta function (Lentz continued-fraction
 * method from Numerical Recipes) to compute exact p-values from the
 * F-distribution.
 */

// ── Numerical helpers ────────────────────────────────────────────────────────

/** Log-gamma via Lanczos approximation (accurate to ~15 sig. figures). */
function lgamma(x: number): number {
  const g = 7;
  const c = [
    0.99999999999980993,
    676.5203681218851,
    -1259.1392167224028,
    771.32342877765313,
    -176.61502916214059,
    12.507343278686905,
    -0.13857109526572012,
    9.9843695780195716e-6,
    1.5056327351493116e-7,
  ];
  if (x < 0.5) {
    return Math.log(Math.PI / Math.sin(Math.PI * x)) - lgamma(1 - x);
  }
  x -= 1;
  let a = c[0];
  const t = x + g + 0.5;
  for (let i = 1; i < g + 2; i++) a += c[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}

/**
 * Regularized incomplete beta function I_x(a,b) via Lentz continued fractions.
 * Returns P(X ≤ x) where X ~ Beta(a, b).
 */
function betainc(x: number, a: number, b: number): number {
  if (x <= 0) return 0;
  if (x >= 1) return 1;

  // Use symmetry for better convergence when x > (a+1)/(a+b+2)
  if (x > (a + 1) / (a + b + 2)) {
    return 1 - betainc(1 - x, b, a);
  }

  const lbeta = lgamma(a) + lgamma(b) - lgamma(a + b);
  const front = Math.exp(a * Math.log(x) + b * Math.log(1 - x) - lbeta) / a;

  // Lentz's continued fraction
  const MAXIT = 300;
  const EPS = 3e-12;
  const TINY = 1e-300;

  let c = 1.0;
  let d = 1.0 - (a + b) * x / (a + 1);
  if (Math.abs(d) < TINY) d = TINY;
  d = 1 / d;
  let h = d;

  for (let m = 1; m <= MAXIT; m++) {
    // Even step
    let aa = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m));
    d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY;
    c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY;
    d = 1 / d;
    h *= d * c;

    // Odd step
    aa = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1));
    d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY;
    c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY;
    d = 1 / d;
    const delta = d * c;
    h *= delta;

    if (Math.abs(delta - 1) < EPS) break;
  }

  return front * h;
}

/**
 * P-value for F(df1, df2) using the relationship with the beta distribution:
 *   P(F > f) = I_{df2/(df2 + df1·f)}(df2/2, df1/2)
 */
function fPValue(f: number, df1: number, df2: number): number {
  if (!isFinite(f) || f <= 0) return 1;
  const x = df2 / (df2 + df1 * f);
  return betainc(x, df2 / 2, df1 / 2);
}

// ── ANOVA types ──────────────────────────────────────────────────────────────

export interface AnovaEffect {
  SS: number;       // sum of squares
  df: number;       // degrees of freedom
  MS: number;       // mean square (SS/df)
  F: number;        // F-statistic
  p: number;        // p-value
  d: number;        // Cohen's d effect size (derived from F and n)
  significant: boolean;  // p < 0.05
}

export interface AnovaResult {
  /** Main effect of explanation style (clinical vs analogy) */
  style: AnovaEffect;
  /** Main effect of interaction mode (static vs dialog) */
  mode: AnovaEffect;
  /** Style × Mode interaction */
  interaction: AnovaEffect;
  error: { SS: number; df: number; MS: number };
  /** Total observations used */
  n: number;
  /** Cell means for the interaction plot */
  cellMeans: {
    clinicalStatic: number | null;
    clinicalDialog: number | null;
    analogyStatic: number | null;
    analogyDialog: number | null;
  };
  cellN: {
    clinicalStatic: number;
    clinicalDialog: number;
    analogyStatic: number;
    analogyDialog: number;
  };
}

// ── Main computation ─────────────────────────────────────────────────────────

function cellStats(values: number[]): { mean: number; ss: number; n: number } {
  const n = values.length;
  if (n === 0) return { mean: 0, ss: 0, n: 0 };
  const mean = values.reduce((a, b) => a + b, 0) / n;
  const ss = values.reduce((s, v) => s + (v - mean) ** 2, 0);
  return { mean, ss, n };
}

/**
 * Run a 2×2 factorial ANOVA.
 * Returns null if there are fewer than 5 total observations or any cell is empty.
 */
export function anova2x2(
  clinicalStatic: number[],
  clinicalDialog: number[],
  analogyStatic: number[],
  analogyDialog: number[],
): AnovaResult | null {
  const cells = [clinicalStatic, clinicalDialog, analogyStatic, analogyDialog];
  const stats = cells.map(cellStats);
  const [cs, cd, as_, ad] = stats;

  // Need at least one obs per cell and df_error > 0
  if (stats.some((s) => s.n === 0)) return null;
  const n = stats.reduce((t, s) => t + s.n, 0);
  const df_error = n - 4;
  if (df_error <= 0) return null;

  // Grand mean (weighted)
  const grandMean = stats.reduce((s, c) => s + c.mean * c.n, 0) / n;

  // Marginal means (weighted by cell n)
  const nClinical = cs.n + cd.n;
  const nAnalogy = as_.n + ad.n;
  const nStatic = cs.n + as_.n;
  const nDialog = cd.n + ad.n;

  const mClinical = (cs.mean * cs.n + cd.mean * cd.n) / nClinical;
  const mAnalogy = (as_.mean * as_.n + ad.mean * ad.n) / nAnalogy;
  const mStatic = (cs.mean * cs.n + as_.mean * as_.n) / nStatic;
  const mDialog = (cd.mean * cd.n + ad.mean * ad.n) / nDialog;

  // SS_A (style), SS_B (mode)
  const SS_A = nClinical * (mClinical - grandMean) ** 2 + nAnalogy * (mAnalogy - grandMean) ** 2;
  const SS_B = nStatic * (mStatic - grandMean) ** 2 + nDialog * (mDialog - grandMean) ** 2;

  // SS_cells (between-group variance across all 4 cells)
  const SS_cells = stats.reduce((s, c) => s + c.n * (c.mean - grandMean) ** 2, 0);

  // SS_AB (interaction) = SS_cells - SS_A - SS_B
  const SS_AB = SS_cells - SS_A - SS_B;

  // SS_error (within-group variance)
  const SS_error = stats.reduce((s, c) => s + c.ss, 0);

  const MS_error = SS_error / df_error;

  function makeEffect(SS: number, df: number, n1: number, n2: number): AnovaEffect {
    const MS = SS / df;
    const F = MS_error > 0 ? MS / MS_error : 0;
    const p = fPValue(F, df, df_error);
    // Cohen's d from F: d = sqrt(F * (1/n1 + 1/n2))
    const d = F > 0 ? Math.sqrt(F * (1 / n1 + 1 / n2)) : 0;
    return { SS, df, MS, F, p, d, significant: p < 0.05 };
  }

  return {
    style: makeEffect(SS_A, 1, nClinical, nAnalogy),
    mode: makeEffect(SS_B, 1, nStatic, nDialog),
    interaction: makeEffect(Math.max(SS_AB, 0), 1, nClinical, nAnalogy),
    error: { SS: SS_error, df: df_error, MS: MS_error },
    n,
    cellMeans: {
      clinicalStatic: cs.n > 0 ? cs.mean : null,
      clinicalDialog: cd.n > 0 ? cd.mean : null,
      analogyStatic: as_.n > 0 ? as_.mean : null,
      analogyDialog: ad.n > 0 ? ad.mean : null,
    },
    cellN: {
      clinicalStatic: cs.n,
      clinicalDialog: cd.n,
      analogyStatic: as_.n,
      analogyDialog: ad.n,
    },
  };
}