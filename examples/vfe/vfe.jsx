import React, { useState, useMemo, useEffect } from 'react';
import { ChevronDown, ChevronRight, AlertCircle, CheckCircle } from 'lucide-react';

/*
================================================================================
VARIATIONAL FREE ENERGY - PERCEPTION SIMULATION
================================================================================

MATHEMATICAL FRAMEWORK (Gaussian Case)
--------------------------------------

Generative Model:
  - Prior:      P(s)   = N(s; μₚ, σₚ²)     "Expected state distribution"
  - Likelihood: P(o|s) = N(o; s, σₒ²)      "How states generate observations"
  
Recognition Model:
  - Approximate posterior: Q(s) = N(s; μᵩ, σᵩ²)  "Belief about the hidden state"

================================================================================
FREE ENERGY VS SURPRISE: KEY RELATIONSHIP
================================================================================

SURPRISE (Negative Log Evidence):
  S = -log P(o) = -log ∫ P(o|s)P(s) ds
  
  This is the "true" surprise - how unexpected the observation is under the 
  generative model. It requires integrating over all possible hidden states,
  which is often intractable.

VARIATIONAL FREE ENERGY:
  F = D_KL[Q(s) || P(s)] + E_Q[-log P(o|s)]
    = Complexity          + Negative Accuracy
  
  This is a computable upper bound on Surprise.

THE FUNDAMENTAL RELATIONSHIP:
  
  F = -log P(o) + D_KL[Q(s) || P(s|o)]
    = Surprise  + Divergence from true posterior
  
  Therefore:  F ≥ Surprise  (always!)
  
  The gap (F - Surprise) = D_KL[Q(s) || P(s|o)] ≥ 0
  
  This gap measures how far the approximate posterior Q(s) is from the 
  true Bayesian posterior P(s|o). When Q(s) = P(s|o) exactly, the gap 
  is zero and F = Surprise.

WHY USE FREE ENERGY?
  1. Surprise is often intractable (requires marginalization)
  2. Free Energy is always computable given Q
  3. Minimizing F simultaneously:
     - Minimizes Surprise (better model of observations)
     - Makes Q closer to true posterior (better inference)

IN THIS SIMULATION:
  Because we use Gaussians, we can compute both F and Surprise exactly.
  At the optimal Q (true Bayesian posterior), F = Surprise.
  In manual mode, you can make Q suboptimal and see F > Surprise.

================================================================================
*/

// =============================================================================
// COLOR SCHEME - Consistent variable coloring
// =============================================================================
const COLORS = {
  // Variables (used consistently throughout)
  prior: '#D97706',      // amber-600: μₚ, σₚ, πₚ, P(s)
  sensory: '#2563EB',    // blue-600: o, σₒ, πₒ, P(o|s)
  posterior: '#059669',  // emerald-600: μᵩ, σᵩ, πᵩ, Q(s)
  energy: '#7C3AED',     // violet-600: F, KL, Accuracy
  
  // UI (grayscale)
  bg: '#111827',         // gray-900
  panel: '#1F2937',      // gray-800
  border: '#374151',     // gray-700
  text: '#E5E7EB',       // gray-200
  textMuted: '#9CA3AF',  // gray-400
  textDim: '#6B7280',    // gray-500
};

// =============================================================================
// MATHEMATICAL FUNCTIONS (with validation)
// =============================================================================

/**
 * Gaussian probability density function
 * p(x|μ,σ) = (1/(σ√(2π))) · exp(-½((x-μ)/σ)²)
 */
const gaussianPDF = (x, mu, sigma) => {
  if (sigma <= 0) return 0;
  const coef = 1 / (sigma * Math.sqrt(2 * Math.PI));
  const exponent = -0.5 * Math.pow((x - mu) / sigma, 2);
  return coef * Math.exp(exponent);
};

/**
 * KL Divergence between two Gaussians: D_KL[N(μ_q,σ_q) || N(μ_p,σ_p)]
 * 
 * Formula: log(σₚ/σᵩ) + (σᵩ² + (μᵩ - μₚ)²)/(2σₚ²) - ½
 * 
 * Derivation:
 *   D_KL = ∫ Q(s) log(Q(s)/P(s)) ds
 *        = E_Q[log Q(s)] - E_Q[log P(s)]
 *        = -H(Q) - E_Q[log P(s)]
 *   
 *   For Gaussians:
 *   -H(Q) = -½(1 + log(2πσᵩ²))
 *   E_Q[log P(s)] = -½log(2πσₚ²) - E_Q[(s-μₚ)²]/(2σₚ²)
 *                 = -½log(2πσₚ²) - (σᵩ² + (μᵩ-μₚ)²)/(2σₚ²)
 */
const klDivergence = (mu_q, sigma_q, mu_p, sigma_p) => {
  if (sigma_q <= 0 || sigma_p <= 0) return Infinity;
  
  const logRatio = Math.log(sigma_p / sigma_q);
  const varianceTerm = sigma_q * sigma_q;
  const meanDiffSq = Math.pow(mu_q - mu_p, 2);
  const denominator = 2 * sigma_p * sigma_p;
  
  return logRatio + (varianceTerm + meanDiffSq) / denominator - 0.5;
};

/**
 * Expected Negative Log Likelihood: E_Q[-log P(o|s)]
 * 
 * Where P(o|s) = N(o; s, σₒ²) means "observation o given state s"
 * 
 * Formula: ½log(2π) + log(σₒ) + (σᵩ² + (μᵩ - o)²)/(2σₒ²)
 * 
 * Derivation:
 *   -log P(o|s) = ½log(2π) + log(σₒ) + (o-s)²/(2σₒ²)
 *   
 *   E_Q[(o-s)²] = E_Q[o² - 2os + s²]
 *               = o² - 2o·μᵩ + E_Q[s²]
 *               = o² - 2o·μᵩ + (σᵩ² + μᵩ²)
 *               = (o - μᵩ)² + σᵩ²
 */
const negLogLikelihood = (o, mu_q, sigma_q, sigma_o) => {
  if (sigma_o <= 0 || sigma_q < 0) return Infinity;
  
  const constTerm = 0.5 * Math.log(2 * Math.PI);
  const logSigma = Math.log(sigma_o);
  const predErrorSq = Math.pow(mu_q - o, 2);
  const varianceTerm = sigma_q * sigma_q;
  const denominator = 2 * sigma_o * sigma_o;
  
  return constTerm + logSigma + (varianceTerm + predErrorSq) / denominator;
};

/**
 * Compute optimal Bayesian posterior (minimizes Free Energy)
 * 
 * Posterior P(s|o) ∝ P(o|s)·P(s)
 * 
 * For Gaussians, this gives:
 *   πᵩ = πₚ + πₒ                           [precisions add]
 *   μᵩ = (πₚ·μₚ + πₒ·o) / (πₚ + πₒ)        [precision-weighted mean]
 *   σᵩ = 1/√πᵩ
 */
const computeOptimalPosterior = (o, mu_p, pi_p, pi_o) => {
  if (pi_p <= 0 || pi_o <= 0) return { mu_q: o, sigma_q: 1, pi_q: 1 };
  
  const pi_q = pi_p + pi_o;
  const mu_q = (pi_p * mu_p + pi_o * o) / pi_q;
  const sigma_q = 1 / Math.sqrt(pi_q);
  
  return { mu_q, sigma_q, pi_q };
};

/**
 * Surprise (Negative Log Evidence): -log P(o)
 * 
 * P(o) = ∫ P(o|s)P(s) ds = N(o; μₚ, σₚ² + σₒ²)
 * 
 * This is the convolution of two Gaussians.
 * 
 * Formula: ½log(2π(σₚ² + σₒ²)) + (o - μₚ)²/(2(σₚ² + σₒ²))
 * 
 * IMPORTANT: Surprise depends ONLY on:
 *   - observation (o)
 *   - prior mean (μₚ)
 *   - prior variance (σₚ²)
 *   - observation variance (σₒ²)
 * 
 * Surprise does NOT depend on the posterior Q(s) or μᵩ.
 * Therefore, Surprise remains constant when manually adjusting μᵩ in manual mode.
 * This is mathematically correct: Surprise measures how unexpected the observation
 * is under the generative model, independent of our beliefs about the hidden state.
 */
const computeSurprise = (o, mu_p, sigma_p, sigma_o) => {
  const totalVariance = sigma_p * sigma_p + sigma_o * sigma_o;
  const constTerm = 0.5 * Math.log(2 * Math.PI * totalVariance);
  const predErrorSq = Math.pow(o - mu_p, 2);
  
  return constTerm + predErrorSq / (2 * totalVariance);
};

/**
 * Compute F at arbitrary μᵩ (for landscape plot)
 */
const computeFAtMu = (mu_q, sigma_q, o, mu_p, sigma_p, sigma_o) => {
  const complexity = klDivergence(mu_q, sigma_q, mu_p, sigma_p);
  const negAccuracy = negLogLikelihood(o, mu_q, sigma_q, sigma_o);
  return { complexity, negAccuracy, freeEnergy: complexity + negAccuracy };
};

// =============================================================================
// VALIDATION & CHECKS
// =============================================================================

const validateComputation = (computed, priorPrecision, sensoryPrecision, observation, priorMean) => {
  const checks = [];
  
  // Check 1: F ≥ Surprise (fundamental bound)
  const boundHolds = computed.freeEnergy >= computed.surprise - 1e-10;
  checks.push({
    name: 'F ≥ Surprise',
    passed: boundHolds,
    detail: `${computed.freeEnergy.toFixed(4)} ≥ ${computed.surprise.toFixed(4)}`,
  });
  
  // Check 2: KL ≥ 0 (KL divergence is non-negative)
  const klNonNeg = computed.complexity >= -1e-10;
  checks.push({
    name: 'KL ≥ 0',
    passed: klNonNeg,
    detail: `KL = ${computed.complexity.toFixed(4)}`,
  });
  
  // Check 3: Precision weights sum to 1
  const weightsSum = computed.priorWeight + computed.sensoryWeight;
  const weightsSumTo1 = Math.abs(weightsSum - 1) < 1e-10;
  checks.push({
    name: 'Weights sum to 1',
    passed: weightsSumTo1,
    detail: `${computed.priorWeight.toFixed(3)} + ${computed.sensoryWeight.toFixed(3)} = ${weightsSum.toFixed(6)}`,
  });
  
  // Check 4: Posterior mean between prior and observation
  const muBetween = (computed.mu_q >= Math.min(priorMean, observation) - 1e-10) && 
                    (computed.mu_q <= Math.max(priorMean, observation) + 1e-10);
  checks.push({
    name: 'μᵩ between μₚ and o',
    passed: muBetween,
    detail: `μₚ=${priorMean.toFixed(2)}, μᵩ=${computed.mu_q.toFixed(2)}, o=${observation.toFixed(2)}`,
  });
  
  // Check 5: Posterior precision = sum of precisions
  const piSum = priorPrecision + sensoryPrecision;
  const piCorrect = Math.abs(computed.optimal.pi_q - piSum) < 1e-10;
  checks.push({
    name: 'πᵩ = πₚ + πₒ',
    passed: piCorrect,
    detail: `${priorPrecision.toFixed(2)} + ${sensoryPrecision.toFixed(2)} = ${piSum.toFixed(2)}`,
  });
  
  // Check 6: At optimal, prediction errors are precision-weighted balanced
  const weightedPE = sensoryPrecision * computed.sensoryPE + priorPrecision * (-computed.priorPE);
  const peBalanced = Math.abs(weightedPE) < 1e-8;
  checks.push({
    name: 'πₒ·εₒ = πₚ·εₚ (at optimal)',
    passed: peBalanced,
    detail: `Balance: ${weightedPE.toFixed(6)}`,
  });
  
  return checks;
};

// =============================================================================
// UI COMPONENTS
// =============================================================================

const Section = ({ title, children, defaultOpen = true, hint = null }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  return (
    <div className="border rounded-lg mb-2 overflow-hidden" style={{ borderColor: COLORS.border, backgroundColor: COLORS.panel }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-2 hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isOpen ? <ChevronDown size={16} color={COLORS.textMuted} /> : <ChevronRight size={16} color={COLORS.textMuted} />}
          <span className="font-medium text-sm" style={{ color: COLORS.text }}>{title}</span>
        </div>
        {hint && <span className="text-xs" style={{ color: COLORS.textDim }}>{hint}</span>}
      </button>
      <div className={`transition-all duration-200 ${isOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
        <div className="p-3 pt-1 border-t" style={{ borderColor: COLORS.border }}>
          {children}
        </div>
      </div>
    </div>
  );
};

// Subscript helper
const Sub = ({ children }) => <sub className="text-xs">{children}</sub>;

// Variable display with consistent coloring
const V = ({ type, children }) => (
  <span style={{ color: COLORS[type] || COLORS.text }} className="font-mono">{children}</span>
);

// Distribution Plot
const DistributionPlot = ({ distributions, xRange, height = 160, width = 340 }) => {
  const points = 120;
  const [xMin, xMax] = xRange;
  const step = (xMax - xMin) / points;
  
  let maxY = 0;
  const allData = distributions.map(d => {
    const data = [];
    for (let i = 0; i <= points; i++) {
      const x = xMin + i * step;
      const y = gaussianPDF(x, d.mu, d.sigma);
      data.push({ x, y });
      if (y > maxY) maxY = y;
    }
    return { ...d, data };
  });
  maxY *= 1.1;
  
  const margin = { top: 10, right: 10, bottom: 28, left: 35 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  const xScale = (x) => margin.left + ((x - xMin) / (xMax - xMin)) * innerWidth;
  const yScale = (y) => margin.top + innerHeight - (y / maxY) * innerHeight;
  
  return (
    <svg width={width} height={height} style={{ backgroundColor: COLORS.bg }} className="rounded">
      {[0, 0.5, 1].map(t => (
        <line key={t} x1={margin.left} x2={width - margin.right}
          y1={margin.top + t * innerHeight} y2={margin.top + t * innerHeight}
          stroke={COLORS.border} strokeWidth="1" />
      ))}
      
      <line x1={margin.left} x2={width - margin.right} y1={height - margin.bottom} y2={height - margin.bottom} stroke={COLORS.textDim} />
      <line x1={margin.left} x2={margin.left} y1={margin.top} y2={height - margin.bottom} stroke={COLORS.textDim} />
      
      <text x={width / 2} y={height - 6} textAnchor="middle" fill={COLORS.textMuted} fontSize="11">
        hidden state s
      </text>
      <text x={14} y={height / 2} textAnchor="middle" fill={COLORS.textMuted} fontSize="10" 
        transform={`rotate(-90, 14, ${height / 2})`}>density</text>
      
      {allData.map((d, idx) => {
        const pathData = d.data.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${xScale(pt.x)} ${yScale(pt.y)}`).join(' ');
        return (
          <g key={idx}>
            <path d={`${pathData} L ${xScale(d.data[d.data.length-1].x)} ${yScale(0)} L ${xScale(d.data[0].x)} ${yScale(0)} Z`}
              fill={d.color} opacity={0.12} />
            <path d={pathData} fill="none" stroke={d.color} strokeWidth="2.5" />
            <line x1={xScale(d.mu)} x2={xScale(d.mu)} y1={yScale(0)} y2={yScale(gaussianPDF(d.mu, d.mu, d.sigma))} 
              stroke={d.color} strokeWidth="1.5" strokeDasharray="4,3" opacity="0.7" />
          </g>
        );
      })}
      
      {allData.map((d, idx) => (
        <g key={`leg-${idx}`} transform={`translate(${margin.left + 5}, ${margin.top + 12 + idx * 15})`}>
          <rect x="-3" y="-9" width={d.label.length * 5.5 + 25} height="13" fill={COLORS.bg} opacity="0.85" rx="2" />
          <line x1="0" x2="14" y1="0" y2="0" stroke={d.color} strokeWidth="2.5" />
          <text x="18" y="3" fill={d.color} fontSize="10" fontWeight="500">{d.label}</text>
        </g>
      ))}
    </svg>
  );
};

// Free Energy Landscape
const FreeEnergyLandscape = ({ o, mu_p, sigma_p, sigma_o, sigma_q, currentMu, optimalMu, width = 340, height = 150 }) => {
  const margin = { top: 12, right: 10, bottom: 28, left: 42 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  const muRange = [-5, 5];
  const points = 100;
  const step = (muRange[1] - muRange[0]) / points;
  
  const data = [];
  let minF = Infinity, maxF = -Infinity;
  
  for (let i = 0; i <= points; i++) {
    const mu = muRange[0] + i * step;
    const { freeEnergy } = computeFAtMu(mu, sigma_q, o, mu_p, sigma_p, sigma_o);
    data.push({ mu, freeEnergy });
    if (freeEnergy < minF) minF = freeEnergy;
    if (freeEnergy > maxF) maxF = freeEnergy;
  }
  maxF = Math.min(maxF, minF + 8);
  
  const xScale = (x) => margin.left + ((x - muRange[0]) / (muRange[1] - muRange[0])) * innerWidth;
  const yScale = (y) => margin.top + innerHeight - ((Math.min(y, maxF) - minF) / (maxF - minF)) * innerHeight;
  
  const fPath = data.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${xScale(pt.mu)} ${yScale(pt.freeEnergy)}`).join(' ');
  
  const currentF = computeFAtMu(currentMu, sigma_q, o, mu_p, sigma_p, sigma_o).freeEnergy;
  const optimalF = computeFAtMu(optimalMu, sigma_q, o, mu_p, sigma_p, sigma_o).freeEnergy;
  const isSuboptimal = Math.abs(currentMu - optimalMu) > 0.05;
  
  return (
    <svg width={width} height={height} style={{ backgroundColor: COLORS.bg }} className="rounded">
      <line x1={margin.left} x2={width - margin.right} y1={height - margin.bottom} y2={height - margin.bottom} stroke={COLORS.textDim} />
      <line x1={margin.left} x2={margin.left} y1={margin.top} y2={height - margin.bottom} stroke={COLORS.textDim} />
      
      <line x1={xScale(mu_p)} x2={xScale(mu_p)} y1={margin.top} y2={height - margin.bottom} 
        stroke={COLORS.prior} strokeWidth="1.5" strokeDasharray="4,4" opacity="0.6" />
      <text x={xScale(mu_p)} y={margin.top + 10} textAnchor="middle" fill={COLORS.prior} fontSize="9">μₚ</text>
      
      <line x1={xScale(o)} x2={xScale(o)} y1={margin.top} y2={height - margin.bottom} 
        stroke={COLORS.sensory} strokeWidth="1.5" strokeDasharray="4,4" opacity="0.6" />
      <text x={xScale(o)} y={margin.top + 10} textAnchor="middle" fill={COLORS.sensory} fontSize="9">o</text>
      
      <path d={fPath} fill="none" stroke={COLORS.energy} strokeWidth="2.5" />
      
      <circle cx={xScale(optimalMu)} cy={yScale(optimalF)} r="7" fill={COLORS.posterior} stroke="#fff" strokeWidth="2" />
      <text x={xScale(optimalMu)} y={yScale(optimalF) - 12} textAnchor="middle" fill={COLORS.posterior} fontSize="10" fontWeight="500">
        μᵩ*
      </text>
      
      {isSuboptimal && (
        <>
          <line x1={xScale(optimalMu)} x2={xScale(currentMu)} y1={yScale(optimalF)} y2={yScale(currentF)}
            stroke="#EF4444" strokeWidth="1.5" strokeDasharray="4,3" />
          <circle cx={xScale(currentMu)} cy={yScale(currentF)} r="6" fill="#EF4444" stroke="#fff" strokeWidth="1.5" />
          <text x={xScale(currentMu)} y={yScale(currentF) - 10} textAnchor="middle" fill="#EF4444" fontSize="9">
            μᵩ (manual)
          </text>
        </>
      )}
      
      <text x={width / 2} y={height - 6} textAnchor="middle" fill={COLORS.textMuted} fontSize="11">
        belief μᵩ
      </text>
      <text x={16} y={height / 2} textAnchor="middle" fill={COLORS.energy} fontSize="10" 
        transform={`rotate(-90, 16, ${height / 2})`}>Free Energy F</text>
    </svg>
  );
};

// Complexity-Accuracy Trade-off
const TradeoffPlot = ({ history, current, width = 300, height = 180 }) => {
  const margin = { top: 15, right: 10, bottom: 32, left: 48 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  const allPoints = [...history, current];
  const maxC = Math.max(...allPoints.map(p => p.complexity), 0.5);
  const maxA = Math.max(...allPoints.map(p => p.negAccuracy), 0.5);
  
  const xScale = (x) => margin.left + (x / maxC) * innerWidth;
  const yScale = (y) => margin.top + innerHeight - (y / maxA) * innerHeight;
  
  const maxF = maxC + maxA;
  const isoFValues = [0.5, 1, 2, 3, 4, 5, 6, 8, 10].filter(f => f <= maxF * 1.2);
  
  return (
    <svg width={width} height={height} style={{ backgroundColor: COLORS.bg }} className="rounded">
      {isoFValues.map(f => {
        const x1 = Math.min(f, maxC);
        const y1 = Math.max(0, f - x1);
        const x2 = Math.max(0, f - maxA);
        const y2 = Math.min(maxA, f - x2);
        if (y1 > maxA || x2 > maxC || y2 < 0) return null;
        return (
          <g key={f}>
            <line x1={xScale(x1)} y1={yScale(y1)} x2={xScale(x2)} y2={yScale(y2)} 
              stroke={COLORS.border} strokeWidth="1" strokeDasharray="5,5" />
            <text x={xScale(Math.min(f * 0.55, maxC * 0.9))} y={yScale(Math.min(f * 0.45, maxA * 0.9)) - 4} 
              fill={COLORS.textDim} fontSize="9">F={f}</text>
          </g>
        );
      })}
      
      <line x1={margin.left} x2={width - margin.right} y1={height - margin.bottom} y2={height - margin.bottom} stroke={COLORS.textDim} />
      <line x1={margin.left} x2={margin.left} y1={margin.top} y2={height - margin.bottom} stroke={COLORS.textDim} />
      
      {history.length > 1 && (
        <path d={history.map((p, i) => `${i === 0 ? 'M' : 'L'} ${xScale(p.complexity)} ${yScale(p.negAccuracy)}`).join(' ')}
          fill="none" stroke={COLORS.textDim} strokeWidth="1" opacity="0.4" />
      )}
      {history.map((p, i) => (
        <circle key={i} cx={xScale(p.complexity)} cy={yScale(p.negAccuracy)} 
          r="2.5" fill={COLORS.textDim} opacity={0.15 + (i / history.length) * 0.6} />
      ))}
      
      <circle cx={xScale(current.complexity)} cy={yScale(current.negAccuracy)} 
        r="7" fill={COLORS.energy} stroke="#fff" strokeWidth="2" />
      
      <text x={width / 2} y={height - 6} textAnchor="middle" fontSize="11">
        <tspan fill={COLORS.textMuted}>Complexity </tspan>
        <tspan fill={COLORS.prior}>D</tspan>
        <tspan fill={COLORS.prior} fontSize="8" dy="2">KL</tspan>
        <tspan dy="-2" fill={COLORS.prior}>[Q||P(s)]</tspan>
      </text>
      <text x={16} y={height / 2} textAnchor="middle" fontSize="11" transform={`rotate(-90, 16, ${height / 2})`}>
        <tspan fill={COLORS.textMuted}>−Accuracy </tspan>
        <tspan fill={COLORS.sensory}>E</tspan>
        <tspan fill={COLORS.sensory} fontSize="8" dy="2">Q</tspan>
        <tspan dy="-2" fill={COLORS.sensory}>[−log P(o|s)]</tspan>
      </text>
    </svg>
  );
};

// Precision Weighting Bars
const PrecisionBar = ({ priorWeight, sensoryWeight, priorPrecision, sensoryPrecision }) => (
  <div className="space-y-2">
    <div className="flex items-center gap-2">
      <span className="text-xs w-20 text-right" style={{ color: COLORS.prior }}>
        Prior (πₚ={priorPrecision.toFixed(1)})
      </span>
      <div className="flex-1 rounded h-5 overflow-hidden" style={{ backgroundColor: COLORS.border }}>
        <div className="h-full transition-all duration-200 flex items-center justify-end pr-2"
          style={{ width: `${priorWeight * 100}%`, backgroundColor: COLORS.prior }}>
          <span className="text-xs text-white font-mono font-bold">{(priorWeight * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
    <div className="flex items-center gap-2">
      <span className="text-xs w-20 text-right" style={{ color: COLORS.sensory }}>
        Sensory (πₒ={sensoryPrecision.toFixed(1)})
      </span>
      <div className="flex-1 rounded h-5 overflow-hidden" style={{ backgroundColor: COLORS.border }}>
        <div className="h-full transition-all duration-200 flex items-center justify-end pr-2"
          style={{ width: `${sensoryWeight * 100}%`, backgroundColor: COLORS.sensory }}>
          <span className="text-xs text-white font-mono font-bold">{(sensoryWeight * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
    <p className="text-xs italic" style={{ color: COLORS.textDim }}>
      Posterior μᵩ is pulled toward the source with higher precision
    </p>
  </div>
);

// Dynamic Equation Display - FIXED: F also scales, bars scale to actual max
const DynamicEquation = ({ complexity, negAccuracy, freeEnergy, priorPrecision, sensoryPrecision, 
                           mu_q, mu_p, o, sigma_q, sigma_p, sigma_o }) => {
  // Scale factors based on magnitudes - all three terms scale
  // Ensure maxTerm is at least 0.1 to avoid division issues
  const maxTerm = Math.max(Math.abs(complexity), Math.abs(negAccuracy), Math.abs(freeEnergy), 0.1);
  // Scale range: 0.7 (minimum) to 1.2 (maximum when term equals maxTerm)
  // This ensures the largest term is visually prominent
  const complexityScale = 0.7 + (Math.abs(complexity) / maxTerm) * 0.5;
  const accuracyScale = 0.7 + (Math.abs(negAccuracy) / maxTerm) * 0.5;
  const freeEnergyScale = 0.7 + (Math.abs(freeEnergy) / maxTerm) * 0.5;
  
  // Verify: when freeEnergy is the max, freeEnergyScale should be 1.2
  // This ensures Free Energy box scales properly when it's the dominant term
  
  const totalPrecision = priorPrecision + sensoryPrecision;
  const priorScale = 0.85 + (priorPrecision / totalPrecision) * 0.4;
  const sensoryScale = 0.85 + (sensoryPrecision / totalPrecision) * 0.4;
  
  // KL breakdown terms
  const klTerm1 = Math.log(sigma_p / sigma_q);
  const klTerm2_num = sigma_q * sigma_q + Math.pow(mu_q - mu_p, 2);
  const klTerm2_den = 2 * sigma_p * sigma_p;
  
  return (
    <div className="space-y-4">
      {/* Main F = Complexity + NegAccuracy */}
      <div>
        <div className="text-xs mb-2" style={{ color: COLORS.textDim }}>
          Free Energy Decomposition (all box sizes ∝ relative magnitude):
        </div>
        <div className="flex items-center justify-center gap-3 flex-wrap py-2">
          <div className="transition-all duration-300 origin-center" style={{ transform: `scale(${freeEnergyScale})` }}>
            <span className="font-bold text-2xl" style={{ color: COLORS.energy }}>F</span>
          </div>
          <span className="text-xl" style={{ color: COLORS.textDim }}>=</span>
          
          <div className="transition-all duration-300 origin-center" style={{ transform: `scale(${complexityScale})` }}>
            <div className="rounded-lg px-4 py-2 text-center border-2" 
              style={{ backgroundColor: `${COLORS.prior}15`, borderColor: COLORS.prior }}>
              <div className="text-xs font-medium" style={{ color: COLORS.prior }}>Complexity</div>
              <div className="text-xs" style={{ color: COLORS.textDim }}>D<Sub>KL</Sub>[Q||P(s)]</div>
              <div className="font-mono font-bold text-xl" style={{ color: COLORS.prior }}>{complexity.toFixed(3)}</div>
            </div>
          </div>
          
          <span className="text-2xl" style={{ color: COLORS.textDim }}>+</span>
          
          <div className="transition-all duration-300 origin-center" style={{ transform: `scale(${accuracyScale})` }}>
            <div className="rounded-lg px-4 py-2 text-center border-2"
              style={{ backgroundColor: `${COLORS.sensory}15`, borderColor: COLORS.sensory }}>
              <div className="text-xs font-medium" style={{ color: COLORS.sensory }}>Neg. Accuracy</div>
              <div className="text-xs" style={{ color: COLORS.textDim }}>E<Sub>Q</Sub>[−log P(o|s)]</div>
              <div className="font-mono font-bold text-xl" style={{ color: COLORS.sensory }}>{negAccuracy.toFixed(3)}</div>
            </div>
          </div>
          
          <span className="text-xl" style={{ color: COLORS.textDim }}>=</span>
          
          <div className="transition-all duration-300 origin-center" style={{ transform: `scale(${freeEnergyScale})` }}>
            <div className="rounded-lg px-4 py-2 text-center border-2"
              style={{ backgroundColor: `${COLORS.energy}15`, borderColor: COLORS.energy }}>
              <div className="text-xs font-medium" style={{ color: COLORS.energy }}>Free Energy</div>
              <div className="font-mono font-bold text-2xl" style={{ color: COLORS.energy }}>{freeEnergy.toFixed(3)}</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Bayesian Update Equation */}
      <div className="border-t pt-3" style={{ borderColor: COLORS.border }}>
        <div className="text-xs mb-2" style={{ color: COLORS.textDim }}>
          Precision-Weighted Bayesian Update (term size ∝ weight):
        </div>
        <div className="flex items-center justify-center gap-2 flex-wrap rounded-lg py-3 px-2"
          style={{ backgroundColor: `${COLORS.bg}` }}>
          <div className="text-center">
            <div className="text-xs" style={{ color: COLORS.posterior }}>optimal belief</div>
            <div className="font-mono text-lg font-bold" style={{ color: COLORS.posterior }}>
              μᵩ* = {mu_q.toFixed(3)}
            </div>
          </div>
          
          <span style={{ color: COLORS.textDim }}>=</span>
          <span style={{ color: COLORS.textDim }}>(</span>
          
          <div className="transition-all duration-300 origin-center" style={{ transform: `scale(${priorScale})` }}>
            <div className="rounded px-2 py-1 border" style={{ backgroundColor: `${COLORS.prior}20`, borderColor: COLORS.prior }}>
              <div className="font-mono text-sm" style={{ color: COLORS.prior }}>
                <span className="text-xs">πₚ</span> × <span className="text-xs">μₚ</span>
              </div>
              <div className="font-mono text-sm font-bold" style={{ color: COLORS.prior }}>
                {priorPrecision.toFixed(1)} × {mu_p.toFixed(1)} = {(priorPrecision * mu_p).toFixed(2)}
              </div>
            </div>
          </div>
          
          <span style={{ color: COLORS.textDim }}>+</span>
          
          <div className="transition-all duration-300 origin-center" style={{ transform: `scale(${sensoryScale})` }}>
            <div className="rounded px-2 py-1 border" style={{ backgroundColor: `${COLORS.sensory}20`, borderColor: COLORS.sensory }}>
              <div className="font-mono text-sm" style={{ color: COLORS.sensory }}>
                <span className="text-xs">πₒ</span> × <span className="text-xs">o</span>
              </div>
              <div className="font-mono text-sm font-bold" style={{ color: COLORS.sensory }}>
                {sensoryPrecision.toFixed(1)} × {o.toFixed(1)} = {(sensoryPrecision * o).toFixed(2)}
              </div>
            </div>
          </div>
          
          <span style={{ color: COLORS.textDim }}>)</span>
          <span style={{ color: COLORS.textDim }}>/</span>
          <span className="font-mono" style={{ color: COLORS.text }}>{totalPrecision.toFixed(1)}</span>
        </div>
      </div>
      
      {/* KL Breakdown */}
      <div className="border-t pt-3" style={{ borderColor: COLORS.border }}>
        <div className="text-xs mb-2" style={{ color: COLORS.textDim }}>
          KL Divergence Breakdown:
        </div>
        <div className="rounded-lg p-2" style={{ backgroundColor: COLORS.bg }}>
          <div className="text-xs font-mono text-center mb-2" style={{ color: COLORS.textMuted }}>
            D<Sub>KL</Sub>[Q||P] = log(σₚ/σᵩ) + (σᵩ² + (μᵩ − μₚ)²) / (2σₚ²) − ½
          </div>
          <div className="flex justify-center gap-2 flex-wrap text-xs font-mono">
            <div className="rounded px-2 py-1" style={{ backgroundColor: COLORS.panel }}>
              <span style={{ color: COLORS.textDim }}>log(</span>
              <span style={{ color: COLORS.prior }}>{sigma_p.toFixed(2)}</span>
              <span style={{ color: COLORS.textDim }}>/</span>
              <span style={{ color: COLORS.posterior }}>{sigma_q.toFixed(2)}</span>
              <span style={{ color: COLORS.textDim }}>) = </span>
              <span style={{ color: COLORS.prior }}>{klTerm1.toFixed(4)}</span>
            </div>
            <div className="rounded px-2 py-1" style={{ backgroundColor: COLORS.panel }}>
              <span style={{ color: COLORS.textDim }}>(</span>
              <span style={{ color: COLORS.posterior }}>{sigma_q.toFixed(2)}</span>
              <span style={{ color: COLORS.textDim }}>² + </span>
              <span style={{ color: COLORS.textDim }}>(</span>
              <span style={{ color: COLORS.posterior }}>{mu_q.toFixed(2)}</span>
              <span style={{ color: COLORS.textDim }}> − </span>
              <span style={{ color: COLORS.prior }}>{mu_p.toFixed(2)}</span>
              <span style={{ color: COLORS.textDim }}>)²) / {klTerm2_den.toFixed(2)} = </span>
              <span style={{ color: COLORS.prior }}>{(klTerm2_num / klTerm2_den).toFixed(4)}</span>
            </div>
            <div className="rounded px-2 py-1" style={{ backgroundColor: COLORS.panel }}>
              <span style={{ color: COLORS.textDim }}>− 0.5</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Energy Bars - FIXED: scales to actual maximum value
const EnergyBars = ({ complexity, negAccuracy, freeEnergy, surprise }) => {
  // Use the actual maximum value in the data, ensure it's at least a small positive value
  const maxVal = Math.max(complexity, negAccuracy, freeEnergy, surprise, 0.01);
  // Scale function: ensures max value is always 100%, others scale proportionally
  const scale = (v) => {
    if (maxVal <= 0) return '0%';
    const percentage = (v / maxVal) * 100;
    // Clamp between 0 and 100 to ensure max is exactly 100%
    return `${Math.min(Math.max(percentage, 0), 100)}%`;
  };
  
  const bars = [
    { label: 'Complexity', sublabel: 'D_KL[Q||P(s)]', value: complexity, color: COLORS.prior },
    { label: 'Neg. Accuracy', sublabel: 'E_Q[−log P(o|s)]', value: negAccuracy, color: COLORS.sensory },
    { label: 'Free Energy F', sublabel: '(upper bound)', value: freeEnergy, color: COLORS.energy },
    { label: 'Surprise', sublabel: '−log P(o)', value: surprise, color: COLORS.textDim },
  ];
  
  return (
    <div className="space-y-2">
      {bars.map((bar, i) => {
        // Find if this bar has the maximum value
        const isMax = bar.value === maxVal || Math.abs(bar.value - maxVal) < 1e-10;
        const barWidth = isMax ? '100%' : scale(bar.value);
        
        return (
          <div key={i} className="flex items-center gap-2">
            <div className="w-28 text-right">
              <div className="text-xs font-medium" style={{ color: bar.color }}>{bar.label}</div>
              <div className="text-xs" style={{ color: COLORS.textDim }}>{bar.sublabel}</div>
            </div>
            <div className="flex-1 rounded h-5 overflow-hidden" style={{ backgroundColor: COLORS.border }}>
              <div className="h-full transition-all duration-200" style={{ width: barWidth, backgroundColor: bar.color }} />
            </div>
            <span className="font-mono text-sm w-20 text-right" style={{ color: bar.color }}>{bar.value.toFixed(4)}</span>
          </div>
        );
      })}
      <div className="text-xs text-center mt-2 p-2 rounded" style={{ backgroundColor: COLORS.bg, color: COLORS.textMuted }}>
        <strong>Gap:</strong> F − Surprise = <span style={{ color: COLORS.energy }}>{(freeEnergy - surprise).toFixed(6)}</span>
        {freeEnergy - surprise < 0.0001 ? 
          <span style={{ color: COLORS.posterior }}> ≈ 0 (Q is optimal!)</span> : 
          <span style={{ color: COLORS.textDim }}> &gt; 0 (Q is suboptimal)</span>
        }
      </div>
    </div>
  );
};

// Prediction Errors
const PredictionErrors = ({ sensoryPE, priorPE, o, mu_q, mu_p, pi_o, pi_p }) => {
  const weightedSensory = pi_o * sensoryPE;
  const weightedPrior = pi_p * priorPE;
  
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="w-24 text-right">
          <div className="text-xs font-medium" style={{ color: COLORS.sensory }}>Sensory PE</div>
          <div className="text-xs" style={{ color: COLORS.textDim }}>εₒ = o − μᵩ</div>
        </div>
        <div className="flex-1 flex items-center gap-2 flex-wrap">
          <span className="font-mono text-sm" style={{ color: COLORS.sensory }}>
            {o.toFixed(2)} − {mu_q.toFixed(2)}
          </span>
          <span style={{ color: COLORS.textDim }}>=</span>
          <span className="font-mono font-bold" style={{ color: COLORS.sensory }}>
            {sensoryPE >= 0 ? '+' : ''}{sensoryPE.toFixed(3)}
          </span>
          <span className="text-xs" style={{ color: COLORS.textDim }}>
            (weighted: πₒ·εₒ = {weightedSensory.toFixed(3)})
          </span>
        </div>
      </div>
      
      <div className="flex items-center gap-3 flex-wrap">
        <div className="w-24 text-right">
          <div className="text-xs font-medium" style={{ color: COLORS.prior }}>Prior PE</div>
          <div className="text-xs" style={{ color: COLORS.textDim }}>εₚ = μᵩ − μₚ</div>
        </div>
        <div className="flex-1 flex items-center gap-2 flex-wrap">
          <span className="font-mono text-sm" style={{ color: COLORS.prior }}>
            {mu_q.toFixed(2)} − {mu_p.toFixed(2)}
          </span>
          <span style={{ color: COLORS.textDim }}>=</span>
          <span className="font-mono font-bold" style={{ color: COLORS.prior }}>
            {priorPE >= 0 ? '+' : ''}{priorPE.toFixed(3)}
          </span>
          <span className="text-xs" style={{ color: COLORS.textDim }}>
            (weighted: πₚ·εₚ = {weightedPrior.toFixed(3)})
          </span>
        </div>
      </div>
      
      <div className="rounded p-2 text-xs" style={{ backgroundColor: COLORS.bg }}>
        <div style={{ color: COLORS.textMuted }}>
          <strong>At optimum:</strong> πₒ·εₒ = πₚ·εₚ (precision-weighted prediction errors balance)
        </div>
        <div className="font-mono mt-1" style={{ color: COLORS.textDim }}>
          Currently: {Math.abs(weightedSensory).toFixed(4)} vs {Math.abs(weightedPrior).toFixed(4)} 
          &nbsp;(difference: {Math.abs(weightedSensory - weightedPrior).toFixed(6)})
        </div>
      </div>
    </div>
  );
};

// Validation Panel
const ValidationPanel = ({ checks }) => (
  <div className="space-y-1">
    {checks.map((check, i) => (
      <div key={i} className="flex items-center gap-2 text-xs">
        {check.passed ? 
          <CheckCircle size={14} color={COLORS.posterior} /> : 
          <AlertCircle size={14} color="#EF4444" />
        }
        <span style={{ color: check.passed ? COLORS.posterior : '#EF4444' }} className="font-medium">
          {check.name}
        </span>
        <span style={{ color: COLORS.textDim }} className="font-mono">{check.detail}</span>
      </div>
    ))}
  </div>
);

// F vs Surprise Explanation Component
const FvsSurpriseExplanation = ({ freeEnergy, surprise, complexity, negAccuracy, isOptimal }) => {
  const gap = freeEnergy - surprise;
  
  return (
    <div className="space-y-3 text-sm">
      <div className="rounded p-3" style={{ backgroundColor: COLORS.bg }}>
        <h4 className="font-medium mb-2" style={{ color: COLORS.energy }}>What is Free Energy?</h4>
        <p style={{ color: COLORS.textMuted }}>
          <strong>Variational Free Energy (F)</strong> is a quantity that any system can compute given:
        </p>
        <ul className="list-disc list-inside mt-1 space-y-1" style={{ color: COLORS.textDim }}>
          <li>Its beliefs about hidden states: <V type="posterior">Q(s)</V></li>
          <li>Its generative model: <V type="prior">P(s)</V> and <V type="sensory">P(o|s)</V></li>
          <li>Current observations: <V type="sensory">o</V></li>
        </ul>
      </div>
      
      <div className="rounded p-3" style={{ backgroundColor: COLORS.bg }}>
        <h4 className="font-medium mb-2" style={{ color: COLORS.textMuted }}>What is Surprise?</h4>
        <p style={{ color: COLORS.textMuted }}>
          <strong>Surprise</strong> (negative log evidence) measures how unexpected an observation is:
        </p>
        <div className="font-mono text-center my-2" style={{ color: COLORS.text }}>
          S = −log P(o) = −log ∫ P(o|s)P(s) ds
        </div>
        <p style={{ color: COLORS.textDim }}>
          This integral over all hidden states is often <em>intractable</em> to compute directly.
        </p>
      </div>
      
      <div className="rounded p-3 border-2" style={{ backgroundColor: `${COLORS.energy}10`, borderColor: COLORS.energy }}>
        <h4 className="font-medium mb-2" style={{ color: COLORS.energy }}>The Key Relationship</h4>
        <div className="font-mono text-center my-2" style={{ color: COLORS.text }}>
          <V type="energy">F</V> = <span style={{ color: COLORS.textMuted }}>Surprise</span> + D<Sub>KL</Sub>[<V type="posterior">Q(s)</V> || P(s|o)]
        </div>
        <p style={{ color: COLORS.textMuted }}>
          Free Energy equals Surprise <em>plus</em> the KL divergence between the approximate 
          posterior Q(s) and the true posterior P(s|o).
        </p>
        <div className="mt-2 p-2 rounded" style={{ backgroundColor: COLORS.panel }}>
          <p style={{ color: COLORS.text }}>
            <strong>Since KL ≥ 0 always:</strong> <V type="energy">F ≥ Surprise</V>
          </p>
          <p className="mt-1" style={{ color: COLORS.textDim }}>
            F is an <em>upper bound</em> on Surprise. Minimizing F implicitly minimizes Surprise.
          </p>
        </div>
      </div>
      
      <div className="rounded p-3" style={{ backgroundColor: COLORS.bg }}>
        <h4 className="font-medium mb-2" style={{ color: COLORS.posterior }}>When Does F = Surprise?</h4>
        <p style={{ color: COLORS.textMuted }}>
          When the approximate posterior <V type="posterior">Q(s)</V> equals the true Bayesian 
          posterior P(s|o), the KL divergence is zero, so F = Surprise exactly.
        </p>
        <div className="mt-2 p-2 rounded font-mono text-sm" style={{ backgroundColor: COLORS.panel }}>
          <div style={{ color: COLORS.textMuted }}>Current values:</div>
          <div><V type="energy">F = {freeEnergy.toFixed(6)}</V></div>
          <div style={{ color: COLORS.textDim }}>Surprise = {surprise.toFixed(6)}</div>
          <div style={{ color: gap < 0.0001 ? COLORS.posterior : '#EF4444' }}>
            Gap = {gap.toFixed(6)} {gap < 0.0001 ? '≈ 0 ✓' : '> 0 (Q suboptimal)'}
          </div>
        </div>
      </div>
      
      <div className="rounded p-3" style={{ backgroundColor: COLORS.bg }}>
        <h4 className="font-medium mb-2" style={{ color: COLORS.textMuted }}>Why Two Decompositions?</h4>
        <p style={{ color: COLORS.textDim }}>
          F can be written two equivalent ways:
        </p>
        <div className="mt-2 space-y-2 font-mono text-xs">
          <div className="p-2 rounded" style={{ backgroundColor: COLORS.panel }}>
            <div style={{ color: COLORS.textMuted }}>1. <strong>Complexity + Accuracy</strong> (tractable):</div>
            <div style={{ color: COLORS.text }}>
              F = <V type="prior">D<Sub>KL</Sub>[Q||P(s)]</V> + <V type="sensory">E<Sub>Q</Sub>[−log P(o|s)]</V>
            </div>
            <div style={{ color: COLORS.textDim }}>
              = {complexity.toFixed(4)} + {negAccuracy.toFixed(4)} = {freeEnergy.toFixed(4)}
            </div>
          </div>
          <div className="p-2 rounded" style={{ backgroundColor: COLORS.panel }}>
            <div style={{ color: COLORS.textMuted }}>2. <strong>Surprise + Posterior Divergence</strong>:</div>
            <div style={{ color: COLORS.text }}>
              F = −log P(o) + D<Sub>KL</Sub>[Q(s) || P(s|o)]
            </div>
            <div style={{ color: COLORS.textDim }}>
              = {surprise.toFixed(4)} + {gap.toFixed(4)} = {freeEnergy.toFixed(4)}
            </div>
          </div>
        </div>
        <p className="mt-2" style={{ color: COLORS.textDim }}>
          Form 1 is what we compute. Form 2 explains <em>why</em> minimizing F is useful.
        </p>
      </div>
    </div>
  );
};

// Slider
const Slider = ({ label, sublabel, value, onChange, min, max, step, color }) => (
  <div className="mb-3">
    <div className="flex justify-between items-baseline mb-1">
      <div>
        <span className="text-sm" style={{ color: COLORS.text }}>{label}</span>
        {sublabel && <span className="text-xs ml-1" style={{ color: COLORS.textDim }}>{sublabel}</span>}
      </div>
      <span style={{ color }} className="font-mono font-bold text-sm">{value.toFixed(2)}</span>
    </div>
    <input type="range" min={min} max={max} step={step} value={value}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      className="w-full h-2 rounded-lg appearance-none cursor-pointer"
      style={{ accentColor: color, backgroundColor: COLORS.border }} />
  </div>
);

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function VFEDashboard() {
  const [observation, setObservation] = useState(2.0);
  const [priorMean, setPriorMean] = useState(0.0);
  const [priorPrecision, setPriorPrecision] = useState(1.0);
  const [sensoryPrecision, setSensoryPrecision] = useState(2.0);
  const [manualMode, setManualMode] = useState(false);
  const [manualMu, setManualMu] = useState(1.0);
  const [history, setHistory] = useState([]);
  
  const computed = useMemo(() => {
    const sigma_p = 1 / Math.sqrt(priorPrecision);
    const sigma_o = 1 / Math.sqrt(sensoryPrecision);
    const optimal = computeOptimalPosterior(observation, priorMean, priorPrecision, sensoryPrecision);
    const mu_q = manualMode ? manualMu : optimal.mu_q;
    const sigma_q = optimal.sigma_q;
    
    const sensoryPE = observation - mu_q;
    const priorPE = mu_q - priorMean;
    
    const complexity = klDivergence(mu_q, sigma_q, priorMean, sigma_p);
    const negAccuracy = negLogLikelihood(observation, mu_q, sigma_q, sigma_o);
    const freeEnergy = complexity + negAccuracy;
    // Surprise = -log P(o) depends only on observation and prior, NOT on mu_q
    // It will recalculate when observation, priorMean, or precisions change
    // but remains constant when manually adjusting mu_q (this is correct behavior)
    const surprise = computeSurprise(observation, priorMean, sigma_p, sigma_o);
    
    const totalPrecision = priorPrecision + sensoryPrecision;
    const priorWeight = priorPrecision / totalPrecision;
    const sensoryWeight = sensoryPrecision / totalPrecision;
    
    return {
      sigma_p, sigma_o, optimal, mu_q, sigma_q,
      sensoryPE, priorPE,
      complexity, negAccuracy, freeEnergy, surprise,
      priorWeight, sensoryWeight
    };
  }, [observation, priorMean, priorPrecision, sensoryPrecision, manualMode, manualMu]);
  
  const validationChecks = useMemo(() => 
    validateComputation(computed, priorPrecision, sensoryPrecision, observation, priorMean),
    [computed, priorPrecision, sensoryPrecision, observation, priorMean]
  );
  
  useEffect(() => {
    setHistory(prev => [...prev, { 
      complexity: computed.complexity, 
      negAccuracy: computed.negAccuracy 
    }].slice(-50));
  }, [computed.complexity, computed.negAccuracy]);
  
  const distributions = [
    { mu: priorMean, sigma: computed.sigma_p, color: COLORS.prior, label: 'P(s) Prior' },
    { mu: observation, sigma: computed.sigma_o, color: COLORS.sensory, label: 'P(o|s) Likelihood' },
    { mu: computed.mu_q, sigma: computed.sigma_q, color: COLORS.posterior, label: 'Q(s) Posterior' },
  ];
  
  const isOptimal = !manualMode || Math.abs(manualMu - computed.optimal.mu_q) < 0.01;
  
  return (
    <div className="min-h-screen p-2" style={{ backgroundColor: COLORS.bg, color: COLORS.text }}>
      {/* Header */}
      <div className="text-center mb-3">
        <h1 className="text-xl font-bold">Variational Free Energy: Perception</h1>
        <p className="text-sm" style={{ color: COLORS.textMuted }}>
          <V type="energy">F</V> = <V type="prior">D<Sub>KL</Sub>[Q||P(s)]</V> + <V type="sensory">E<Sub>Q</Sub>[−log P(o|s)]</V> ≥ Surprise
        </p>
      </div>
      
      <div className="flex flex-col lg:flex-row gap-3 max-w-7xl mx-auto">
        {/* Left: Controls (sticky) */}
        <div className="lg:w-80 lg:sticky lg:top-2 lg:self-start">
          <div className="rounded-lg p-3" style={{ backgroundColor: COLORS.panel }}>
            <h2 className="text-sm font-semibold mb-2" style={{ color: COLORS.textMuted }}>Model Parameters</h2>
            
            <Section title="Sensory Input" defaultOpen={true} hint="observation o">
              <Slider label="o" sublabel="observation" value={observation} onChange={setObservation}
                min={-5} max={5} step={0.1} color={COLORS.sensory} />
              <Slider label="πₒ" sublabel="sensory precision (1/σₒ²)" value={sensoryPrecision} onChange={setSensoryPrecision}
                min={0.1} max={10} step={0.1} color={COLORS.sensory} />
              <p className="text-xs" style={{ color: COLORS.textDim }}>
                High <V type="sensory">πₒ</V> → trust sensory data, posterior → observation
              </p>
            </Section>
            
            <Section title="Prior Beliefs" defaultOpen={true} hint="expectation μₚ">
              <Slider label="μₚ" sublabel="prior mean" value={priorMean} onChange={setPriorMean}
                min={-5} max={5} step={0.1} color={COLORS.prior} />
              <Slider label="πₚ" sublabel="prior precision (1/σₚ²)" value={priorPrecision} onChange={setPriorPrecision}
                min={0.1} max={10} step={0.1} color={COLORS.prior} />
              <p className="text-xs" style={{ color: COLORS.textDim }}>
                High <V type="prior">πₚ</V> → strong prior, posterior → prior mean
              </p>
            </Section>
            
            <Section title="Manual Exploration" defaultOpen={false} hint="test suboptimality">
              <div className="flex items-center gap-2 mb-2">
                <input type="checkbox" id="manual" checked={manualMode} 
                  onChange={(e) => setManualMode(e.target.checked)} 
                  style={{ accentColor: COLORS.posterior }} />
                <label htmlFor="manual" className="text-xs" style={{ color: COLORS.textMuted }}>
                  Override optimal belief
                </label>
              </div>
              {manualMode && (
                <Slider label="μᵩ" sublabel="manual belief (suboptimal)" value={manualMu} onChange={setManualMu}
                  min={-5} max={5} step={0.1} color="#EF4444" />
              )}
              <p className="text-xs" style={{ color: COLORS.textDim }}>
                Drag <V type="posterior">μᵩ</V> away from optimal to see F &gt; Surprise
              </p>
            </Section>
            
            <Section title="Precision Weights" defaultOpen={true}>
              <PrecisionBar priorWeight={computed.priorWeight} sensoryWeight={computed.sensoryWeight}
                priorPrecision={priorPrecision} sensoryPrecision={sensoryPrecision} />
            </Section>
          </div>
        </div>
        
        {/* Right: Visualizations */}
        <div className="flex-1 space-y-2">
          {/* NEW: F vs Surprise Explanation Section */}
          <Section title="Free Energy vs Surprise: What's the Difference?" defaultOpen={true} hint="key concept">
            <FvsSurpriseExplanation 
              freeEnergy={computed.freeEnergy} 
              surprise={computed.surprise}
              complexity={computed.complexity}
              negAccuracy={computed.negAccuracy}
              isOptimal={isOptimal}
            />
          </Section>
          
          <Section title="Probability Distributions" defaultOpen={true} hint="P(s) × P(o|s) → Q(s)">
            <div className="flex flex-wrap gap-4 items-start">
              <DistributionPlot distributions={distributions} xRange={[-6, 6]} width={360} height={170} />
              <div className="text-xs space-y-2 flex-1 min-w-[200px]">
                <div className="font-medium" style={{ color: COLORS.textMuted }}>Bayesian Inference:</div>
                <div><V type="prior">P(s) = N(μₚ={priorMean.toFixed(2)}, σₚ={computed.sigma_p.toFixed(3)})</V></div>
                <div><V type="sensory">P(o|s) ∝ N(s; o={observation.toFixed(2)}, σₒ={computed.sigma_o.toFixed(3)})</V></div>
                <div><V type="posterior">Q(s) = N(μᵩ={computed.mu_q.toFixed(3)}, σᵩ={computed.sigma_q.toFixed(3)})</V></div>
                <div className="p-2 rounded mt-2" style={{ backgroundColor: COLORS.bg }}>
                  The posterior <V type="posterior">Q(s)</V> is the precision-weighted compromise between 
                  <V type="prior"> prior</V> and <V type="sensory"> likelihood</V>.
                </div>
              </div>
            </div>
          </Section>
          
          <Section title="Free Energy Components" defaultOpen={true} hint="F = Complexity + (−Accuracy)">
            <EnergyBars complexity={computed.complexity} negAccuracy={computed.negAccuracy} 
              freeEnergy={computed.freeEnergy} surprise={computed.surprise} />
          </Section>
          
          <Section title="Dynamic Equations" defaultOpen={true} hint="size ∝ magnitude">
            <DynamicEquation 
              complexity={computed.complexity} negAccuracy={computed.negAccuracy} freeEnergy={computed.freeEnergy}
              priorPrecision={priorPrecision} sensoryPrecision={sensoryPrecision}
              mu_q={computed.mu_q} mu_p={priorMean} o={observation}
              sigma_q={computed.sigma_q} sigma_p={computed.sigma_p} sigma_o={computed.sigma_o}
            />
          </Section>
          
          <Section title="Prediction Errors" defaultOpen={false} hint="εₒ and εₚ">
            <PredictionErrors sensoryPE={computed.sensoryPE} priorPE={computed.priorPE}
              o={observation} mu_q={computed.mu_q} mu_p={priorMean}
              pi_o={sensoryPrecision} pi_p={priorPrecision} />
          </Section>
          
          <Section title="Free Energy Landscape F(μᵩ)" defaultOpen={false} hint="optimization surface">
            <div className="flex flex-wrap gap-4 items-start">
              <FreeEnergyLandscape o={observation} mu_p={priorMean} sigma_p={computed.sigma_p}
                sigma_o={computed.sigma_o} sigma_q={computed.sigma_q}
                currentMu={computed.mu_q} optimalMu={computed.optimal.mu_q} width={360} height={160} />
              <div className="text-xs space-y-1 flex-1 min-w-[180px]" style={{ color: COLORS.textMuted }}>
                <p>Free energy <V type="energy">F</V> as a function of belief <V type="posterior">μᵩ</V>.</p>
                <p>• <V type="posterior">Green dot</V> = optimal μᵩ* (minimum F)</p>
                {manualMode && <p>• <span style={{ color: '#EF4444' }}>Red dot</span> = manual belief (higher F)</p>}
                <p>• Dashed lines: <V type="prior">μₚ</V> and <V type="sensory">o</V></p>
                <p className="mt-2">Minimizing F finds the optimal belief.</p>
              </div>
            </div>
          </Section>
          
          <Section title="Complexity vs Accuracy Trade-off" defaultOpen={false} hint="trajectory">
            <div className="flex flex-wrap gap-4 items-start">
              <TradeoffPlot history={history} 
                current={{ complexity: computed.complexity, negAccuracy: computed.negAccuracy }} 
                width={320} height={180} />
              <div className="text-xs space-y-2 flex-1 min-w-[180px]">
                <p style={{ color: COLORS.textMuted }}>Movement through (Complexity, Accuracy) space.</p>
                <p style={{ color: COLORS.textDim }}>• Diagonal lines = iso-F contours</p>
                <p><V type="energy">• Purple dot</V> = current state</p>
                <p style={{ color: COLORS.textDim }}>• Trail = recent history</p>
                <button onClick={() => setHistory([])} 
                  className="mt-2 text-xs px-2 py-1 rounded"
                  style={{ backgroundColor: COLORS.border }}>
                  Clear Trail
                </button>
              </div>
            </div>
          </Section>
          
          <Section title="Validation Checks" defaultOpen={false} hint="mathematical invariants">
            <ValidationPanel checks={validationChecks} />
          </Section>
          
          <Section title="All Parameters" defaultOpen={false} hint="summary">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded p-2" style={{ backgroundColor: COLORS.bg }}>
                <div style={{ color: COLORS.prior }}>Prior</div>
                <div>μₚ = {priorMean.toFixed(4)}</div>
                <div>σₚ = {computed.sigma_p.toFixed(4)}</div>
                <div>πₚ = {priorPrecision.toFixed(4)}</div>
              </div>
              <div className="rounded p-2" style={{ backgroundColor: COLORS.bg }}>
                <div style={{ color: COLORS.sensory }}>Sensory</div>
                <div>o = {observation.toFixed(4)}</div>
                <div>σₒ = {computed.sigma_o.toFixed(4)}</div>
                <div>πₒ = {sensoryPrecision.toFixed(4)}</div>
              </div>
              <div className="rounded p-2" style={{ backgroundColor: COLORS.bg }}>
                <div style={{ color: COLORS.posterior }}>Posterior</div>
                <div>μᵩ = {computed.mu_q.toFixed(4)}</div>
                <div>σᵩ = {computed.sigma_q.toFixed(4)}</div>
                <div>πᵩ = {computed.optimal.pi_q.toFixed(4)}</div>
              </div>
              <div className="rounded p-2" style={{ backgroundColor: COLORS.bg }}>
                <div style={{ color: COLORS.energy }}>Energies</div>
                <div>F = {computed.freeEnergy.toFixed(4)}</div>
                <div>KL = {computed.complexity.toFixed(4)}</div>
                <div>−Acc = {computed.negAccuracy.toFixed(4)}</div>
                <div>Surprise = {computed.surprise.toFixed(4)}</div>
              </div>
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}