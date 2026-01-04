import React, { useState, useMemo, useEffect } from 'react';
import { ChevronDown, ChevronRight, AlertCircle, CheckCircle, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Square } from 'lucide-react';

/*
================================================================================
EXPECTED FREE ENERGY - ACTION SELECTION IN GRIDWORLD
================================================================================

MATHEMATICAL FRAMEWORK
----------------------

Expected Free Energy (EFE) for action a:
  EFE(a) = Pragmatic Value + Epistemic Value

Pragmatic Value:
  Measures alignment with preference distributions
  Pragmatic(a) = D_KL[P(o|a) || C(o)]
  - P(o|a) = predicted outcome distribution after taking action a
  - C(o) = preference distribution (what the agent wants)
  - Lower KL divergence = better alignment with preferences

Epistemic Value:
  Measures expected information gain
  Epistemic(a) = E[H[P(s|o,a)]] - H[P(s)]
  - Expected reduction in entropy (uncertainty)
  - Higher information gain = better exploration

Action Selection:
  Agent selects action that minimizes EFE, balancing:
  - Preference satisfaction (pragmatic)
  - Information gathering (epistemic)

================================================================================
*/

// =============================================================================
// COLOR SCHEME - Consistent variable coloring
// =============================================================================
const COLORS = {
  // Variables
  action: '#3B82F6',        // blue-500: actions
  temperature: '#EF4444',   // red-500: temperature preferences
  pH: '#10B981',            // emerald-500: pH preferences
  pragmatic: '#F59E0B',     // amber-500: pragmatic value
  epistemic: '#8B5CF6',    // violet-500: epistemic value
  efe: '#EC4899',           // pink-500: total EFE
  
  // UI (grayscale)
  bg: '#111827',            // gray-900
  panel: '#1F2937',         // gray-800
  border: '#374151',        // gray-700
  text: '#E5E7EB',          // gray-200
  textMuted: '#9CA3AF',     // gray-400
  textDim: '#6B7280',       // gray-500
  agent: '#FCD34D',         // yellow-300: agent position
  visited: '#4B5563',       // gray-600: visited tiles
};

// =============================================================================
// GRIDWORLD CONSTANTS
// =============================================================================
const GRID_SIZE = 10;
const TEMPERATURE_CATEGORIES = ['Cold', 'Cool', 'Warm', 'Hot'];
const PH_CATEGORIES = ['Acidic', 'Neutral', 'Basic'];

// Temperature color mapping
const TEMP_COLORS = {
  'Cold': '#3B82F6',   // blue
  'Cool': '#60A5FA',   // light blue
  'Warm': '#F59E0B',   // amber
  'Hot': '#EF4444',    // red
};

// pH color mapping
const PH_COLORS = {
  'Acidic': '#EF4444',  // red
  'Neutral': '#9CA3AF', // gray
  'Basic': '#10B981',   // emerald
};

// =============================================================================
// MATHEMATICAL FUNCTIONS
// =============================================================================

/**
 * Entropy of a probability distribution
 * 
 * Mathematical definition:
 *   H(P) = -Σ p(x) log₂ p(x)
 * 
 * Properties:
 *   - H(P) ≥ 0 (non-negative)
 *   - H(P) = 0 when distribution is deterministic (one outcome has probability 1)
 *   - H(P) is maximized for uniform distribution
 *   - Units: bits (using log base 2)
 * 
 * @param {number[]} probs - Array of probabilities (must sum to 1)
 * @returns {number} Entropy in bits
 */
const entropy = (probs) => {
  if (!Array.isArray(probs) || probs.length === 0) {
    console.warn('entropy: invalid input, returning 0');
    return 0;
  }
  
  let h = 0;
  for (const p of probs) {
    if (p > 0) {
      h -= p * Math.log2(p);
    }
  }
  
  // Validation: entropy should be non-negative
  if (h < 0) {
    console.warn('entropy: computed negative value, clamping to 0', h);
    return 0;
  }
  
  return h;
};

/**
 * KL Divergence (Kullback-Leibler divergence) between two probability distributions
 * 
 * Mathematical definition:
 *   D_KL[P || Q] = Σ p(x) log₂(p(x) / q(x))
 * 
 * Properties:
 *   - D_KL[P || Q] ≥ 0 (non-negative, Gibbs' inequality)
 *   - D_KL[P || Q] = 0 if and only if P = Q
 *   - Not symmetric: D_KL[P || Q] ≠ D_KL[Q || P] in general
 *   - Units: bits (using log base 2)
 * 
 * Interpretation:
 *   Measures the "distance" from distribution Q to distribution P.
 *   In our context: measures how far predicted outcome P(o|a) is from preference C(o).
 * 
 * @param {number[]} p - First probability distribution (target)
 * @param {number[]} q - Second probability distribution (reference)
 * @returns {number} KL divergence in bits, or Infinity if undefined
 */
const klDivergence = (p, q) => {
  if (!Array.isArray(p) || !Array.isArray(q) || p.length !== q.length) {
    console.warn('klDivergence: invalid input dimensions', { pLength: p?.length, qLength: q?.length });
    return Infinity;
  }
  
  let kl = 0;
  for (let i = 0; i < p.length; i++) {
    if (p[i] > 0) {
      if (q[i] <= 0) {
        // KL divergence is undefined when q[i] = 0 but p[i] > 0
        return Infinity;
      }
      kl += p[i] * Math.log2(p[i] / q[i]);
    }
  }
  
  // Validation: KL divergence should be non-negative
  if (kl < -1e-10) {
    console.warn('klDivergence: computed negative value (numerical error)', kl);
    return Math.max(0, kl);
  }
  
  return kl;
};

/**
 * Normalize probability distribution
 */
const normalize = (probs) => {
  const sum = probs.reduce((a, b) => a + b, 0);
  if (sum === 0) return probs.map(() => 1 / probs.length);
  return probs.map(p => p / sum);
};

/**
 * Gaussian probability density function (for preference distributions)
 */
const gaussianPDF = (x, mu, sigma) => {
  if (sigma <= 0) return 0;
  const coef = 1 / (sigma * Math.sqrt(2 * Math.PI));
  const exponent = -0.5 * Math.pow((x - mu) / sigma, 2);
  return coef * Math.exp(exponent);
};

/**
 * Convert continuous preference to discrete category distribution
 */
const preferenceToCategoryDist = (categories, mu, sigma) => {
  const n = categories.length;
  const probs = [];
  const step = 1.0 / n;
  
  for (let i = 0; i < n; i++) {
    const center = (i + 0.5) * step;
    const density = gaussianPDF(center, mu, sigma);
    probs.push(density);
  }
  
  return normalize(probs);
};

// =============================================================================
// GRIDWORLD DATA STRUCTURES
// =============================================================================

/**
 * Generate random gridworld with Temperature and pH values
 */
const generateGridworld = () => {
  const grid = [];
  for (let row = 0; row < GRID_SIZE; row++) {
    const gridRow = [];
    for (let col = 0; col < GRID_SIZE; col++) {
      gridRow.push({
        row,
        col,
        temperature: TEMPERATURE_CATEGORIES[Math.floor(Math.random() * TEMPERATURE_CATEGORIES.length)],
        pH: PH_CATEGORIES[Math.floor(Math.random() * PH_CATEGORIES.length)],
      });
    }
    grid.push(gridRow);
  }
  return grid;
};

/**
 * Initialize agent beliefs (high uncertainty for all tiles)
 */
const initializeBeliefs = () => {
  const beliefs = {};
  for (let row = 0; row < GRID_SIZE; row++) {
    for (let col = 0; col < GRID_SIZE; col++) {
      const key = `${row},${col}`;
      // Uniform distribution = maximum uncertainty
      beliefs[key] = {
        temperature: TEMPERATURE_CATEGORIES.map(() => 1 / TEMPERATURE_CATEGORIES.length),
        pH: PH_CATEGORIES.map(() => 1 / PH_CATEGORIES.length),
      };
    }
  }
  return beliefs;
};

/**
 * Update beliefs after observing a tile
 */
const updateBeliefs = (tile, beliefs) => {
  const key = `${tile.row},${tile.col}`;
  const newBeliefs = { ...beliefs };
  
  // Update to certain belief (observed value)
  newBeliefs[key] = {
    temperature: TEMPERATURE_CATEGORIES.map(cat => cat === tile.temperature ? 1 : 0),
    pH: PH_CATEGORIES.map(cat => cat === tile.pH ? 1 : 0),
  };
  
  return newBeliefs;
};

/**
 * Get tile at position
 */
const getTile = (gridworld, row, col) => {
  if (row < 0 || row >= GRID_SIZE || col < 0 || col >= GRID_SIZE) return null;
  return gridworld[row][col];
};

/**
 * Predict outcome of action (which tile will be visited)
 */
const predictOutcome = (action, agentPos, gridworld) => {
  let newRow = agentPos.row;
  let newCol = agentPos.col;
  
  if (action === 'Up') newRow = Math.max(0, agentPos.row - 1);
  else if (action === 'Down') newRow = Math.min(GRID_SIZE - 1, agentPos.row + 1);
  else if (action === 'Left') newCol = Math.max(0, agentPos.col - 1);
  else if (action === 'Right') newCol = Math.min(GRID_SIZE - 1, agentPos.col + 1);
  // Stay: no change
  
  return getTile(gridworld, newRow, newCol);
};

// =============================================================================
// EFE COMPUTATION
// =============================================================================

/**
 * Compute pragmatic value for an action
 * 
 * Mathematical definition:
 *   Pragmatic(a) = D_KL[P(o|a) || C(o)]
 * 
 * Where:
 *   - P(o|a) = predicted outcome distribution after taking action a
 *   - C(o) = preference distribution (what the agent wants)
 * 
 * In our implementation:
 *   - We use the agent's current belief about the tile as the predicted outcome
 *   - We compute KL divergence separately for Temperature and pH
 *   - Pragmatic value = sum of both KL divergences
 * 
 * Interpretation:
 *   Lower pragmatic value = better alignment with preferences
 *   The agent wants to minimize this value.
 * 
 * @param {Object} predictedTile - The tile that will be visited
 * @param {Object} beliefs - Current belief distributions for all tiles
 * @param {Object} preferences - Preference distributions (Temperature and pH)
 * @param {string} tileKey - Key identifying the tile (e.g., "5,3")
 * @returns {number} Pragmatic value (KL divergence in bits)
 */
const computePragmaticValue = (predictedTile, beliefs, preferences, tileKey) => {
  if (!predictedTile) {
    console.warn('computePragmaticValue: invalid tile');
    return Infinity;
  }
  
  // Get current belief distribution for the tile
  // If tile hasn't been visited, use uniform distribution (maximum uncertainty)
  const tempBelief = beliefs[tileKey]?.temperature || 
    TEMPERATURE_CATEGORIES.map(() => 1 / TEMPERATURE_CATEGORIES.length);
  const pHBelief = beliefs[tileKey]?.pH || 
    PH_CATEGORIES.map(() => 1 / PH_CATEGORIES.length);
  
  // Convert continuous Gaussian preferences to discrete category distributions
  const tempPreference = preferenceToCategoryDist(
    TEMPERATURE_CATEGORIES,
    preferences.temperature.mu,
    preferences.temperature.sigma
  );
  const pHPreference = preferenceToCategoryDist(
    PH_CATEGORIES,
    preferences.pH.mu,
    preferences.pH.sigma
  );
  
  // KL divergence between predicted outcome (belief) and preference
  // Lower divergence = better alignment with preferences
  const tempKL = klDivergence(tempBelief, tempPreference);
  const pHKL = klDivergence(pHBelief, pHPreference);
  
  // Total pragmatic value is sum of both divergences
  const pragmatic = tempKL + pHKL;
  
  // Validation
  if (!isFinite(pragmatic) || pragmatic < 0) {
    console.warn('computePragmaticValue: invalid result', { tempKL, pHKL, pragmatic });
  }
  
  return pragmatic;
};

/**
 * Compute epistemic value (expected information gain) for an action
 * 
 * Mathematical definition:
 *   Epistemic(a) = E[H[P(s|o,a)]] - H[P(s)]
 *   = H[P(s)] - H[P(s|o,a)]  (expected reduction in entropy)
 * 
 * In our implementation:
 *   - H[P(s)] = current entropy of beliefs about the tile
 *   - H[P(s|o,a)] = entropy after observing the tile (becomes 0, perfect certainty)
 *   - Epistemic value = current entropy (information gain from perfect observation)
 * 
 * Interpretation:
 *   Higher epistemic value = more information will be gained
 *   The agent wants to maximize this value (exploration).
 * 
 * @param {string} action - Action to evaluate
 * @param {Object} agentPos - Current agent position {row, col}
 * @param {Object} beliefs - Current belief distributions for all tiles
 * @param {Array} gridworld - The gridworld environment
 * @returns {number} Epistemic value (information gain in bits)
 */
const computeEpistemicValue = (action, agentPos, beliefs, gridworld) => {
  const predictedTile = predictOutcome(action, agentPos, gridworld);
  if (!predictedTile) {
    console.warn('computeEpistemicValue: invalid action outcome');
    return 0;
  }
  
  const tileKey = `${predictedTile.row},${predictedTile.col}`;
  
  // Get current belief distributions (uncertainty before observation)
  // If tile hasn't been visited, use uniform distribution (maximum uncertainty)
  const currentTempBelief = beliefs[tileKey]?.temperature || 
    TEMPERATURE_CATEGORIES.map(() => 1 / TEMPERATURE_CATEGORIES.length);
  const currentPHBelief = beliefs[tileKey]?.pH || 
    PH_CATEGORIES.map(() => 1 / PH_CATEGORIES.length);
  
  // Current entropy (uncertainty) = H[P(s)]
  const tempEntropy = entropy(currentTempBelief);
  const pHEntropy = entropy(currentPHBelief);
  const currentEntropy = tempEntropy + pHEntropy;
  
  // After observing the tile, beliefs become certain (entropy = 0)
  // H[P(s|o,a)] = 0 (perfect certainty)
  const futureEntropy = 0;
  
  // Information gain = reduction in entropy
  // This is the expected information gain from taking the action
  const epistemic = currentEntropy - futureEntropy;
  
  // Validation
  if (epistemic < 0 || !isFinite(epistemic)) {
    console.warn('computeEpistemicValue: invalid result', { currentEntropy, epistemic });
    return Math.max(0, epistemic);
  }
  
  return epistemic;
};

/**
 * Compute EFE for an action
 */
const computeEFE = (action, agentPos, beliefs, preferences, gridworld) => {
  const predictedTile = predictOutcome(action, agentPos, gridworld);
  if (!predictedTile) return { efe: Infinity, pragmatic: Infinity, epistemic: 0 };
  
  const tileKey = `${predictedTile.row},${predictedTile.col}`;
  const pragmatic = computePragmaticValue(predictedTile, beliefs, preferences, tileKey);
  const epistemic = computeEpistemicValue(action, agentPos, beliefs, gridworld);
  
  // EFE = pragmatic + epistemic (both should be minimized, but epistemic is negative of info gain)
  // So we use: EFE = pragmatic - epistemic (minimize EFE = maximize info gain)
  const efe = pragmatic - epistemic;
  
  return { efe, pragmatic, epistemic };
};

/**
 * Compute action posterior from EFE and prior using softmax
 * P(a) = softmax(log(P_prior(a)) - β * EFE(a))
 * where β is a temperature parameter (inverse temperature)
 * 
 * This ensures that actions with non-zero prior get non-zero posterior probability
 * (unless EFE is infinite, which we handle separately)
 * 
 * Uses log-space computation for numerical stability (log-sum-exp trick)
 */
const computeActionPosterior = (actions, efeValues, actionPrior, beta = 1.0) => {
  // Compute logits in log-space: log(prior) - β * EFE
  const logits = actions.map((action, i) => {
    const prior = actionPrior[action] || 0;
    const efe = efeValues[i].efe;
    
    // If prior is zero, logit is -Infinity (posterior will be 0)
    if (prior <= 0) return -Infinity;
    
    // Handle infinite EFE (should not happen, but safety check)
    if (!isFinite(efe)) return -Infinity;
    
    // Logit: log(prior) - β * EFE
    // Lower EFE = higher logit = higher probability
    return Math.log(prior) - beta * efe;
  });
  
  // Find maximum logit for numerical stability (log-sum-exp trick)
  const finiteLogits = logits.filter(x => isFinite(x));
  if (finiteLogits.length === 0) {
    // All actions have zero prior or infinite EFE - return uniform
    return actions.map(() => 1 / actions.length);
  }
  
  const maxLogit = Math.max(...finiteLogits);
  
  // Compute exp(logit_i - maxLogit) for numerical stability, then normalize
  const unnormalized = logits.map(logit => {
    if (!isFinite(logit)) return 0;
    return Math.exp(logit - maxLogit);
  });
  
  const sum = unnormalized.reduce((a, b) => a + b, 0);
  
  // Normalize to get proper probability distribution
  if (sum === 0 || !isFinite(sum)) {
    // Fallback: uniform distribution
    return actions.map(() => 1 / actions.length);
  }
  
  const posterior = unnormalized.map(p => p / sum);
  
  // Validation: ensure probabilities sum to 1 (within floating point precision)
  const posteriorSum = posterior.reduce((a, b) => a + b, 0);
  if (Math.abs(posteriorSum - 1.0) > 1e-10) {
    // Renormalize if needed
    return posterior.map(p => p / posteriorSum);
  }
  
  return posterior;
};

/**
 * Sample action from posterior distribution
 */
const sampleAction = (actions, posterior) => {
  const rand = Math.random();
  let cumsum = 0;
  for (let i = 0; i < actions.length; i++) {
    cumsum += posterior[i];
    if (rand <= cumsum) {
      return actions[i];
    }
  }
  return actions[actions.length - 1];
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

const Sub = ({ children }) => <sub className="text-xs">{children}</sub>;

const V = ({ type, children }) => (
  <span style={{ color: COLORS[type] || COLORS.text }} className="font-mono">{children}</span>
);

// Slider component
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

// Gridworld Visualization
// Displays each tile with clear Temperature and pH indicators using diagonal split
const GridworldVisualization = ({ gridworld, agentPos, visitedTiles, selectedTile, onTileClick, width = 400, height = 400 }) => {
  const margin = 30;
  const availableWidth = width - 2 * margin;
  const availableHeight = height - 2 * margin;
  const tileSize = Math.min(availableWidth / GRID_SIZE, availableHeight / GRID_SIZE);
  const gridWidth = tileSize * GRID_SIZE;
  const gridHeight = tileSize * GRID_SIZE;
  const offsetX = margin + (availableWidth - gridWidth) / 2;
  const offsetY = margin + (availableHeight - gridHeight) / 2;
  
  const handleTileClick = (e, tile) => {
    e.preventDefault();
    e.stopPropagation();
    console.log('Tile clicked:', tile);
    if (onTileClick) {
      onTileClick(tile);
    }
  };
  
  // Get abbreviated labels for Temperature and pH
  const getTempLabel = (temp) => {
    const labels = { 'Cold': 'C', 'Cool': 'c', 'Warm': 'W', 'Hot': 'H' };
    return labels[temp] || temp[0];
  };
  
  const getPHLabel = (pH) => {
    const labels = { 'Acidic': 'A', 'Neutral': 'N', 'Basic': 'B' };
    return labels[pH] || pH[0];
  };
  
  return (
    <svg width={width} height={height} style={{ backgroundColor: COLORS.bg }} className="rounded" viewBox={`0 0 ${width} ${height}`}>
      {gridworld.flat().map((tile) => {
        const x = offsetX + tile.col * tileSize;
        const y = offsetY + tile.row * tileSize;
        const isVisited = visitedTiles.has(`${tile.row},${tile.col}`);
        const isAgent = tile.row === agentPos.row && tile.col === agentPos.col;
        const isSelected = selectedTile && selectedTile.row === tile.row && selectedTile.col === tile.col;
        
        // Get colors for Temperature and pH
        const tempColor = TEMP_COLORS[tile.temperature] || COLORS.textDim;
        const pHColor = PH_COLORS[tile.pH] || COLORS.textDim;
        
        // Base opacity
        const baseOpacity = isVisited ? 0.6 : 0.8;
        
        return (
          <g key={`${tile.row},${tile.col}`}>
            {/* Background rectangle */}
            <rect
              x={x}
              y={y}
              width={tileSize - 1}
              height={tileSize - 1}
              fill={COLORS.bg}
              stroke={isSelected ? COLORS.efe : COLORS.border}
              strokeWidth={isSelected ? 3 : 1}
              onClick={(e) => handleTileClick(e, tile)}
              onMouseEnter={(e) => {
                e.currentTarget.style.cursor = 'pointer';
              }}
              style={{ cursor: 'pointer' }}
            />
            
            {/* Diagonal split: Top-left triangle = Temperature, Bottom-right = pH */}
            <path
              d={`M ${x} ${y} L ${x + tileSize - 1} ${y} L ${x} ${y + tileSize - 1} Z`}
              fill={tempColor}
              opacity={baseOpacity}
              onClick={(e) => handleTileClick(e, tile)}
              style={{ cursor: 'pointer', pointerEvents: 'all' }}
            />
            <path
              d={`M ${x + tileSize - 1} ${y} L ${x + tileSize - 1} ${y + tileSize - 1} L ${x} ${y + tileSize - 1} Z`}
              fill={pHColor}
              opacity={baseOpacity}
              onClick={(e) => handleTileClick(e, tile)}
              style={{ cursor: 'pointer', pointerEvents: 'all' }}
            />
            
            {/* Text labels for Temperature and pH */}
            {tileSize > 15 && (
              <>
                {/* Temperature label (top-left) */}
                <text
                  x={x + 3}
                  y={y + 10}
                  fill={COLORS.bg}
                  fontSize={Math.max(8, tileSize / 5)}
                  fontWeight="bold"
                  style={{ pointerEvents: 'none' }}
                >
                  {getTempLabel(tile.temperature)}
                </text>
                {/* pH label (bottom-right) */}
                <text
                  x={x + tileSize - 5}
                  y={y + tileSize - 3}
                  fill={COLORS.bg}
                  fontSize={Math.max(8, tileSize / 5)}
                  fontWeight="bold"
                  textAnchor="end"
                  style={{ pointerEvents: 'none' }}
                >
                  {getPHLabel(tile.pH)}
                </text>
              </>
            )}
            
            {/* Agent indicator */}
            {isAgent && (
              <circle
                cx={x + tileSize / 2}
                cy={y + tileSize / 2}
                r={tileSize / 4}
                fill={COLORS.agent}
                stroke={COLORS.bg}
                strokeWidth={2}
                style={{ pointerEvents: 'none' }}
              />
            )}
            
            {/* Visited indicator (small dot) */}
            {isVisited && !isAgent && (
              <circle
                cx={x + tileSize - 4}
                cy={y + 4}
                r={2}
                fill={COLORS.visited}
                style={{ pointerEvents: 'none' }}
              />
            )}
          </g>
        );
      })}
    </svg>
  );
};

// Preference Distribution Plot
const PreferenceDistributionPlot = ({ categories, preference, width = 300, height = 150 }) => {
  const margin = { top: 10, right: 10, bottom: 28, left: 35 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  const dist = preferenceToCategoryDist(categories, preference.mu, preference.sigma);
  const maxProb = Math.max(...dist, 0.01);
  
  return (
    <svg width={width} height={height} style={{ backgroundColor: COLORS.bg }} className="rounded">
      {categories.map((cat, i) => {
        const x = margin.left + (i + 0.5) * (innerWidth / categories.length);
        const barHeight = (dist[i] / maxProb) * innerHeight;
        const y = margin.top + innerHeight - barHeight;
        const color = categories === TEMPERATURE_CATEGORIES ? TEMP_COLORS[cat] : PH_COLORS[cat];
        
        return (
          <g key={cat}>
            <rect
              x={x - innerWidth / (categories.length * 2) + 5}
              y={y}
              width={innerWidth / categories.length - 10}
              height={barHeight}
              fill={color}
              opacity={0.7}
            />
            <text
              x={x}
              y={height - margin.bottom + 12}
              textAnchor="middle"
              fill={COLORS.textMuted}
              fontSize="10"
            >
              {cat}
            </text>
            <text
              x={x}
              y={y - 5}
              textAnchor="middle"
              fill={color}
              fontSize="9"
              fontWeight="500"
            >
              {dist[i].toFixed(2)}
            </text>
          </g>
        );
      })}
      <text x={width / 2} y={height - 6} textAnchor="middle" fill={COLORS.textMuted} fontSize="11">
        Category
      </text>
    </svg>
  );
};

// Action Prior/Posterior Visualization
const ActionDistributionPlot = ({ actions, distribution, title, color, width = 300, height = 120 }) => {
  const margin = { top: 10, right: 10, bottom: 28, left: 35 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  const maxProb = Math.max(...distribution, 0.01);
  
  const actionIcons = {
    'Up': ArrowUp,
    'Down': ArrowDown,
    'Left': ArrowLeft,
    'Right': ArrowRight,
    'Stay': Square,
  };
  
  return (
    <div>
      <div className="text-xs mb-2" style={{ color }}>{title}</div>
      <svg width={width} height={height} style={{ backgroundColor: COLORS.bg }} className="rounded">
        {actions.map((action, i) => {
          const x = margin.left + (i + 0.5) * (innerWidth / actions.length);
          const barHeight = (distribution[i] / maxProb) * innerHeight;
          const y = margin.top + innerHeight - barHeight;
          
          return (
            <g key={action}>
              <rect
                x={x - innerWidth / (actions.length * 2) + 5}
                y={y}
                width={innerWidth / actions.length - 10}
                height={barHeight}
                fill={color}
                opacity={0.7}
              />
              <text
                x={x}
                y={height - margin.bottom + 12}
                textAnchor="middle"
                fill={COLORS.textMuted}
                fontSize="9"
              >
                {action}
              </text>
              <text
                x={x}
                y={y - 5}
                textAnchor="middle"
                fill={color}
                fontSize="8"
                fontWeight="500"
              >
                {distribution[i] > 0 && distribution[i] < 0.01 
                  ? distribution[i].toExponential(1) 
                  : distribution[i].toFixed(2)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// EFE Numerical Display with Dynamic Sizing
const EFENumericalDisplay = ({ actions, efeValues, optimalAction }) => {
  const actionIcons = {
    'Up': ArrowUp,
    'Down': ArrowDown,
    'Left': ArrowLeft,
    'Right': ArrowRight,
    'Stay': Square,
  };
  
  // Find min and max EFE for scaling
  const finiteEFEs = efeValues.map(v => v.efe).filter(v => isFinite(v));
  const minEFE = Math.min(...finiteEFEs);
  const maxEFE = Math.max(...finiteEFEs);
  const efeRange = maxEFE - minEFE || 1;
  
  // Calculate font size based on EFE value (inverse relationship - lower EFE = larger font)
  const getFontSize = (efe) => {
    if (!isFinite(efe)) return 12;
    // Normalize: (maxEFE - efe) / range gives higher values for lower EFE
    const normalized = (maxEFE - efe) / efeRange;
    // Scale between 16px (low EFE) and 24px (very low EFE)
    return 16 + normalized * 8;
  };
  
  // Calculate opacity based on EFE (lower EFE = higher opacity)
  const getOpacity = (efe) => {
    if (!isFinite(efe)) return 0.3;
    const normalized = (maxEFE - efe) / efeRange;
    return 0.6 + normalized * 0.4;
  };
  
  return (
    <div className="space-y-3">
      <div className="text-xs mb-2" style={{ color: COLORS.textMuted }}>
        EFE Values (size ∝ 1/EFE, lower is better):
      </div>
      {actions.map((action, i) => {
        const efe = efeValues[i].efe;
        const isOptimal = action === optimalAction;
        const Icon = actionIcons[action] || Square;
        const fontSize = getFontSize(efe);
        const opacity = getOpacity(efe);
        
        return (
          <div
            key={action}
            className="flex items-center gap-3 p-3 rounded border"
            style={{
              backgroundColor: isOptimal ? `${COLORS.efe}15` : COLORS.panel,
              borderColor: isOptimal ? COLORS.efe : COLORS.border,
            }}
          >
            <Icon size={20} color={COLORS.action} />
            <div className="flex-1">
              <div className="text-xs mb-1" style={{ color: COLORS.textMuted }}>
                {action}
              </div>
              <div
                className="font-mono font-bold transition-all"
                style={{
                  color: COLORS.efe,
                  fontSize: `${fontSize}px`,
                  opacity: opacity,
                  lineHeight: 1.2,
                }}
              >
                {isFinite(efe) ? efe.toFixed(4) : '∞'}
              </div>
              <div className="text-xs mt-1 space-x-3" style={{ color: COLORS.textDim }}>
                <span>Pragmatic: {efeValues[i].pragmatic.toFixed(3)}</span>
                <span>Epistemic: {efeValues[i].epistemic.toFixed(3)}</span>
              </div>
            </div>
            {isOptimal && (
              <div className="text-xs px-2 py-1 rounded" style={{ backgroundColor: COLORS.efe, color: COLORS.bg }}>
                Best
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// Action Evaluation Panel
const ActionEvaluationPanel = ({ actions, efeValues, optimalAction, actionPrior, actionPosterior, onActionClick, onSampleAction }) => {
  const maxEFE = Math.max(...efeValues.map(v => Math.abs(v.efe)), 0.01);
  
  const actionIcons = {
    'Up': ArrowUp,
    'Down': ArrowDown,
    'Left': ArrowLeft,
    'Right': ArrowRight,
    'Stay': Square,
  };
  
  return (
    <div className="space-y-3">
      {onSampleAction && (
        <button
          onClick={onSampleAction}
          className="w-full px-3 py-2 rounded text-sm font-medium transition-colors mb-2"
          style={{ backgroundColor: COLORS.efe, color: COLORS.bg }}
        >
          Sample Action from Posterior
        </button>
      )}
      {actions.map((action, i) => {
        const values = efeValues[i];
        const isOptimal = action === optimalAction;
        const Icon = actionIcons[action] || Square;
        
        const efeWidth = Math.min(Math.abs(values.efe) / maxEFE * 100, 100);
        const pragmaticWidth = Math.min(values.pragmatic / maxEFE * 100, 100);
        const epistemicWidth = Math.min(values.epistemic / maxEFE * 100, 100);
        
        return (
          <div
            key={action}
            onClick={() => onActionClick(action)}
            className={`p-2 rounded border cursor-pointer transition-all ${
              isOptimal ? 'border-2' : ''
            }`}
            style={{
              backgroundColor: isOptimal ? `${COLORS.efe}20` : COLORS.panel,
              borderColor: isOptimal ? COLORS.efe : COLORS.border,
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Icon size={16} color={COLORS.action} />
              <span className="font-medium text-sm" style={{ color: COLORS.text }}>
                {action}
              </span>
              {isOptimal && (
                <span className="text-xs px-1 rounded" style={{ backgroundColor: COLORS.efe, color: COLORS.bg }}>
                  Optimal
                </span>
              )}
            </div>
            
            <div className="space-y-1 text-xs">
              <div className="flex items-center gap-2">
                <span className="w-20" style={{ color: COLORS.textDim }}>EFE:</span>
                <div className="flex-1 rounded h-3 overflow-hidden" style={{ backgroundColor: COLORS.border }}>
                  <div
                    className="h-full transition-all"
                    style={{ width: `${efeWidth}%`, backgroundColor: COLORS.efe }}
                  />
                </div>
                <span className="font-mono w-16 text-right" style={{ color: COLORS.efe }}>
                  {values.efe.toFixed(3)}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="w-20" style={{ color: COLORS.textDim }}>Pragmatic:</span>
                <div className="flex-1 rounded h-2 overflow-hidden" style={{ backgroundColor: COLORS.border }}>
                  <div
                    className="h-full transition-all"
                    style={{ width: `${pragmaticWidth}%`, backgroundColor: COLORS.pragmatic }}
                  />
                </div>
                <span className="font-mono w-16 text-right" style={{ color: COLORS.pragmatic }}>
                  {values.pragmatic.toFixed(3)}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="w-20" style={{ color: COLORS.textDim }}>Epistemic:</span>
                <div className="flex-1 rounded h-2 overflow-hidden" style={{ backgroundColor: COLORS.border }}>
                  <div
                    className="h-full transition-all"
                    style={{ width: `${epistemicWidth}%`, backgroundColor: COLORS.epistemic }}
                  />
                </div>
                <span className="font-mono w-16 text-right" style={{ color: COLORS.epistemic }}>
                  {values.epistemic.toFixed(3)}
                </span>
              </div>
              
              <div className="flex items-center gap-2 mt-1 pt-1 border-t" style={{ borderColor: COLORS.border }}>
                <span className="w-20" style={{ color: COLORS.textDim }}>Prior:</span>
                <span className="font-mono text-xs" style={{ color: COLORS.textMuted }}>
                  {actionPrior[action]?.toFixed(2) || '0.00'}
                </span>
                <span className="w-20 ml-auto" style={{ color: COLORS.textDim }}>Posterior:</span>
                <span className="font-mono text-xs font-bold" style={{ color: COLORS.efe }}>
                  {actionPosterior[i] > 0 && actionPosterior[i] < 0.01 
                    ? actionPosterior[i].toExponential(2) 
                    : actionPosterior[i]?.toFixed(3) || '0.00'}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Uncertainty Heatmap
const UncertaintyHeatmap = ({ beliefs, gridworld, selectedTile, onTileClick, width = 400, height = 400 }) => {
  const margin = 30;
  const availableWidth = width - 2 * margin;
  const availableHeight = height - 2 * margin;
  const tileSize = Math.min(availableWidth / GRID_SIZE, availableHeight / GRID_SIZE);
  const gridWidth = tileSize * GRID_SIZE;
  const gridHeight = tileSize * GRID_SIZE;
  const offsetX = margin + (availableWidth - gridWidth) / 2;
  const offsetY = margin + (availableHeight - gridHeight) / 2;
  
  const handleTileClick = (e, tile) => {
    e.preventDefault();
    e.stopPropagation();
    console.log('Uncertainty map tile clicked:', tile);
    if (onTileClick) {
      onTileClick(tile);
    }
  };
  
  // Compute entropy for each tile
  const entropies = [];
  let maxEntropy = 0;
  
  for (let row = 0; row < GRID_SIZE; row++) {
    for (let col = 0; col < GRID_SIZE; col++) {
      const key = `${row},${col}`;
      const tempBelief = beliefs[key]?.temperature || TEMPERATURE_CATEGORIES.map(() => 1 / TEMPERATURE_CATEGORIES.length);
      const pHBelief = beliefs[key]?.pH || PH_CATEGORIES.map(() => 1 / PH_CATEGORIES.length);
      const totalEntropy = entropy(tempBelief) + entropy(pHBelief);
      const tile = gridworld[row][col];
      entropies.push({ row, col, entropy: totalEntropy, tile });
      maxEntropy = Math.max(maxEntropy, totalEntropy);
    }
  }
  
  return (
    <svg width={width} height={height} style={{ backgroundColor: COLORS.bg }} className="rounded" viewBox={`0 0 ${width} ${height}`}>
      {entropies.map(({ row, col, entropy, tile }) => {
        const x = offsetX + col * tileSize;
        const y = offsetY + row * tileSize;
        const intensity = maxEntropy > 0 ? entropy / maxEntropy : 0;
        // Red = high uncertainty, Green = low uncertainty
        const r = Math.floor(255 * intensity);
        const g = Math.floor(255 * (1 - intensity));
        const b = 0;
        const isSelected = selectedTile && selectedTile.row === row && selectedTile.col === col;
        
        return (
          <g key={`${row},${col}`}>
            <rect
              x={x}
              y={y}
              width={tileSize - 1}
              height={tileSize - 1}
              fill={`rgb(${r},${g},${b})`}
              stroke={isSelected ? COLORS.efe : COLORS.border}
              strokeWidth={isSelected ? 3 : 1}
              opacity={0.7}
              onClick={(e) => handleTileClick(e, tile)}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.9';
                e.currentTarget.style.cursor = 'pointer';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '0.7';
              }}
              style={{ cursor: 'pointer' }}
            />
            {isSelected && (
              <rect
                x={x}
                y={y}
                width={tileSize - 1}
                height={tileSize - 1}
                fill="none"
                stroke={COLORS.efe}
                strokeWidth={3}
                opacity={1}
                style={{ pointerEvents: 'none' }}
              />
            )}
          </g>
        );
      })}
    </svg>
  );
};

// Belief Distribution Display
const BeliefDistribution = ({ beliefs, tile, width = 300, height = 200 }) => {
  if (!tile) {
    return (
      <div className="text-xs p-3 rounded text-center" style={{ backgroundColor: COLORS.panel, color: COLORS.textDim }}>
        No tile selected. Please select a tile to view its belief distribution.
      </div>
    );
  }
  
  const key = `${tile.row},${tile.col}`;
  const tempBelief = beliefs[key]?.temperature || TEMPERATURE_CATEGORIES.map(() => 1 / TEMPERATURE_CATEGORIES.length);
  const pHBelief = beliefs[key]?.pH || PH_CATEGORIES.map(() => 1 / PH_CATEGORIES.length);
  
  // Compute entropy for display
  const tempEntropy = entropy(tempBelief);
  const pHEntropy = entropy(pHBelief);
  const totalEntropy = tempEntropy + pHEntropy;
  
  const margin = { top: 10, right: 10, bottom: 28, left: 35 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const halfHeight = innerHeight / 2;
  
  const maxProb = Math.max(...tempBelief, ...pHBelief, 0.01);
  
  return (
    <div>
      <div className="text-xs mb-2 p-2 rounded" style={{ backgroundColor: COLORS.panel, color: COLORS.textMuted }}>
        <div className="font-medium">Beliefs for tile ({tile.row}, {tile.col})</div>
        <div className="mt-1 text-xs" style={{ color: COLORS.textDim }}>
          Entropy: Temp={tempEntropy.toFixed(3)}, pH={pHEntropy.toFixed(3)}, Total={totalEntropy.toFixed(3)}
        </div>
      </div>
      <svg width={width} height={height} style={{ backgroundColor: COLORS.bg }} className="rounded">
        {/* Temperature beliefs */}
        <text x={width / 2} y={margin.top + 12} textAnchor="middle" fill={COLORS.temperature} fontSize="11" fontWeight="500">
          Temperature
        </text>
        {TEMPERATURE_CATEGORIES.map((cat, i) => {
          const x = margin.left + (i + 0.5) * (innerWidth / TEMPERATURE_CATEGORIES.length);
          const barHeight = (tempBelief[i] / maxProb) * halfHeight;
          const y = margin.top + halfHeight - barHeight;
          const color = TEMP_COLORS[cat];
          
          return (
            <g key={cat}>
              <rect
                x={x - innerWidth / (TEMPERATURE_CATEGORIES.length * 2) + 5}
                y={y}
                width={innerWidth / TEMPERATURE_CATEGORIES.length - 10}
                height={barHeight}
                fill={color}
                opacity={0.7}
              />
              <text
                x={x}
                y={margin.top + halfHeight + 12}
                textAnchor="middle"
                fill={COLORS.textMuted}
                fontSize="9"
              >
                {cat}
              </text>
              <text
                x={x}
                y={y - 5}
                textAnchor="middle"
                fill={color}
                fontSize="8"
              >
                {tempBelief[i].toFixed(2)}
              </text>
            </g>
          );
        })}
        
        {/* pH beliefs */}
        <text x={width / 2} y={margin.top + halfHeight + 30} textAnchor="middle" fill={COLORS.pH} fontSize="11" fontWeight="500">
          pH
        </text>
        {PH_CATEGORIES.map((cat, i) => {
          const x = margin.left + (i + 0.5) * (innerWidth / PH_CATEGORIES.length);
          const barHeight = (pHBelief[i] / maxProb) * halfHeight;
          const y = margin.top + halfHeight + 30 + halfHeight - barHeight;
          const color = PH_COLORS[cat];
          
          return (
            <g key={cat}>
              <rect
                x={x - innerWidth / (PH_CATEGORIES.length * 2) + 5}
                y={y}
                width={innerWidth / PH_CATEGORIES.length - 10}
                height={barHeight}
                fill={color}
                opacity={0.7}
              />
              <text
                x={x}
                y={margin.top + halfHeight + 30 + halfHeight + 12}
                textAnchor="middle"
                fill={COLORS.textMuted}
                fontSize="9"
              >
                {cat}
              </text>
              <text
                x={x}
                y={y - 5}
                textAnchor="middle"
                fill={color}
                fontSize="8"
              >
                {pHBelief[i].toFixed(2)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function EFEDashboard() {
  const [gridworld, setGridworld] = useState(() => generateGridworld());
  const [agentPos, setAgentPos] = useState({ row: Math.floor(GRID_SIZE / 2), col: Math.floor(GRID_SIZE / 2) });
  const [beliefs, setBeliefs] = useState(() => initializeBeliefs());
  const [visitedTiles, setVisitedTiles] = useState(new Set([`${Math.floor(GRID_SIZE / 2)},${Math.floor(GRID_SIZE / 2)}`]));
  const [selectedTile, setSelectedTile] = useState(null);
  
  // Preference distributions (Gaussian parameters)
  const [tempPreference, setTempPreference] = useState({ mu: 0.5, sigma: 0.2 });
  const [pHPreference, setPHPreference] = useState({ mu: 0.5, sigma: 0.2 });
  
  // Actions
  const actions = ['Up', 'Down', 'Left', 'Right', 'Stay'];
  
  // Action prior (default: uniform for 4 directions, 0 for Stay)
  const [actionPrior, setActionPrior] = useState(() => {
    const prior = {};
    actions.forEach(action => {
      prior[action] = action === 'Stay' ? 0 : 0.25;
    });
    return prior;
  });
  
  // Beta parameter for posterior computation (inverse temperature)
  const [beta, setBeta] = useState(1.0);
  
  // Compute EFE for all actions
  const efeValues = useMemo(() => {
    const preferences = {
      temperature: tempPreference,
      pH: pHPreference,
    };
    
    return actions.map(action => computeEFE(action, agentPos, beliefs, preferences, gridworld));
  }, [agentPos, beliefs, tempPreference, pHPreference, gridworld]);
  
  // Find optimal action (minimum EFE)
  const optimalAction = useMemo(() => {
    let minEFE = Infinity;
    let optimal = actions[0];
    actions.forEach((action, i) => {
      if (efeValues[i].efe < minEFE) {
        minEFE = efeValues[i].efe;
        optimal = action;
      }
    });
    return optimal;
  }, [efeValues]);
  
  // Compute action posterior from EFE and prior
  const actionPosterior = useMemo(() => {
    return computeActionPosterior(actions, efeValues, actionPrior, beta);
  }, [actions, efeValues, actionPrior, beta]);
  
  // Sample action from posterior
  const sampleAndExecuteAction = () => {
    console.log('Sampling action from posterior:', actionPosterior);
    const sampledAction = sampleAction(actions, actionPosterior);
    console.log('Sampled action:', sampledAction);
    executeAction(sampledAction);
  };
  
  // Log EFE values when they change
  useEffect(() => {
    console.log('EFE Values updated:', actions.map((action, i) => ({
      action,
      efe: efeValues[i].efe,
      pragmatic: efeValues[i].pragmatic,
      epistemic: efeValues[i].epistemic
    })));
    console.log('Optimal action:', optimalAction);
  }, [efeValues, optimalAction, actions]);
  
  // Log posterior when it changes
  useEffect(() => {
    console.log('Action Posterior:', actions.map((action, i) => ({
      action,
      prior: actionPrior[action] || 0,
      posterior: actionPosterior[i]
    })));
  }, [actionPosterior, actionPrior, actions]);
  
  // Handle action execution
  const executeAction = (action) => {
    console.log('Executing action:', action);
    const newTile = predictOutcome(action, agentPos, gridworld);
    if (!newTile) {
      console.warn('Action resulted in invalid tile');
      return;
    }
    
    console.log('Moving to tile:', newTile.row, newTile.col, {
      temperature: newTile.temperature,
      pH: newTile.pH
    });
    
    // Update agent position
    setAgentPos({ row: newTile.row, col: newTile.col });
    
    // Update visited tiles
    const tileKey = `${newTile.row},${newTile.col}`;
    setVisitedTiles(prev => new Set([...prev, tileKey]));
    
    // Update beliefs (observe the tile)
    setBeliefs(prev => {
      const updated = updateBeliefs(newTile, prev);
      console.log('Updated beliefs for tile', tileKey, {
        temperature: updated[tileKey].temperature,
        pH: updated[tileKey].pH
      });
      return updated;
    });
  };
  
  // Reset gridworld
  const resetGridworld = () => {
    console.log('Resetting gridworld');
    const newGrid = generateGridworld();
    setGridworld(newGrid);
    const centerRow = Math.floor(GRID_SIZE / 2);
    const centerCol = Math.floor(GRID_SIZE / 2);
    setAgentPos({ row: centerRow, col: centerCol });
    setBeliefs(initializeBeliefs());
    setVisitedTiles(new Set([`${centerRow},${centerCol}`]));
    setSelectedTile(null);
    console.log('Gridworld reset complete');
  };
  
  // Log tile selection
  useEffect(() => {
    if (selectedTile) {
      console.log('Tile selected:', selectedTile);
      const key = `${selectedTile.row},${selectedTile.col}`;
      const tileBeliefs = beliefs[key];
      if (tileBeliefs) {
        console.log('Beliefs for selected tile:', {
          temperature: tileBeliefs.temperature,
          pH: tileBeliefs.pH
        });
      }
    }
  }, [selectedTile, beliefs]);
  
  return (
    <div className="min-h-screen p-2" style={{ backgroundColor: COLORS.bg, color: COLORS.text }}>
      {/* Header */}
      <div className="text-center mb-3">
        <h1 className="text-xl font-bold">Expected Free Energy: Gridworld Action Selection</h1>
        <p className="text-sm" style={{ color: COLORS.textMuted }}>
          <V type="efe">EFE(a)</V> = <V type="pragmatic">Pragmatic</V> + <V type="epistemic">Epistemic</V>
        </p>
      </div>
      
      <div className="flex flex-col lg:flex-row gap-3 max-w-7xl mx-auto">
        {/* Left: Controls */}
        <div className="lg:w-80 lg:sticky lg:top-2 lg:self-start">
          <div className="rounded-lg p-3" style={{ backgroundColor: COLORS.panel }}>
            <h2 className="text-sm font-semibold mb-2" style={{ color: COLORS.textMuted }}>Controls</h2>
            
            <Section title="Preference Distributions" defaultOpen={true}>
              <div className="mb-3">
                <div className="text-xs mb-2" style={{ color: COLORS.temperature }}>Temperature</div>
                <Slider
                  label="μ"
                  sublabel="mean"
                  value={tempPreference.mu}
                  onChange={(val) => setTempPreference(prev => ({ ...prev, mu: val }))}
                  min={0}
                  max={1}
                  step={0.01}
                  color={COLORS.temperature}
                />
                <Slider
                  label="σ"
                  sublabel="std dev"
                  value={tempPreference.sigma}
                  onChange={(val) => setTempPreference(prev => ({ ...prev, sigma: val }))}
                  min={0.05}
                  max={0.5}
                  step={0.01}
                  color={COLORS.temperature}
                />
              </div>
              
              <div>
                <div className="text-xs mb-2" style={{ color: COLORS.pH }}>pH</div>
                <Slider
                  label="μ"
                  sublabel="mean"
                  value={pHPreference.mu}
                  onChange={(val) => setPHPreference(prev => ({ ...prev, mu: val }))}
                  min={0}
                  max={1}
                  step={0.01}
                  color={COLORS.pH}
                />
                <Slider
                  label="σ"
                  sublabel="std dev"
                  value={pHPreference.sigma}
                  onChange={(val) => setPHPreference(prev => ({ ...prev, sigma: val }))}
                  min={0.05}
                  max={0.5}
                  step={0.01}
                  color={COLORS.pH}
                />
              </div>
            </Section>
            
            <Section title="Action Prior" defaultOpen={true} hint="P(a)">
              <div className="space-y-2 mb-3">
                {actions.map(action => (
                  <div key={action} className="flex items-center gap-2">
                    <span className="text-xs w-16" style={{ color: COLORS.textMuted }}>{action}:</span>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.01}
                      value={actionPrior[action] || 0}
                      onChange={(e) => setActionPrior(prev => ({ ...prev, [action]: parseFloat(e.target.value) }))}
                      className="flex-1 h-2 rounded-lg appearance-none cursor-pointer"
                      style={{ accentColor: COLORS.action, backgroundColor: COLORS.border }}
                    />
                    <span className="font-mono text-xs w-12 text-right" style={{ color: COLORS.action }}>
                      {actionPrior[action]?.toFixed(2) || '0.00'}
                    </span>
                  </div>
                ))}
              </div>
              <button
                onClick={() => {
                  const uniform = {};
                  actions.forEach(action => {
                    uniform[action] = action === 'Stay' ? 0 : 0.25;
                  });
                  setActionPrior(uniform);
                }}
                className="w-full px-2 py-1 rounded text-xs transition-colors mb-2"
                style={{ backgroundColor: COLORS.border, color: COLORS.text }}
              >
                Reset to Uniform (0.25)
              </button>
              <div className="text-xs mb-2" style={{ color: COLORS.textDim }}>
                Sum: {Object.values(actionPrior).reduce((a, b) => a + b, 0).toFixed(2)}
              </div>
              <ActionDistributionPlot
                actions={actions}
                distribution={actions.map(a => actionPrior[a] || 0)}
                title="Prior Distribution"
                color={COLORS.action}
                width={300}
                height={120}
              />
            </Section>
            
            <Section title="Action Posterior" defaultOpen={true} hint="P(a|EFE)">
              <div className="mb-2">
                <div className="flex justify-between items-baseline mb-1">
                  <span className="text-xs" style={{ color: COLORS.text }}>β (inverse temperature):</span>
                  <span className="font-mono text-xs font-bold" style={{ color: COLORS.efe }}>
                    {beta.toFixed(2)}
                  </span>
                </div>
                <input
                  type="range"
                  min={0.1}
                  max={5}
                  step={0.1}
                  value={beta}
                  onChange={(e) => setBeta(parseFloat(e.target.value))}
                  className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                  style={{ accentColor: COLORS.efe, backgroundColor: COLORS.border }}
                />
                <div className="text-xs mt-1 space-y-1" style={{ color: COLORS.textDim }}>
                  <div>Higher β = more deterministic (focus on low EFE actions)</div>
                  <div>Lower β = more exploratory (more uniform distribution)</div>
                </div>
              </div>
              <ActionDistributionPlot
                actions={actions}
                distribution={actionPosterior}
                title="Posterior: P(a) = softmax(log(P_prior(a)) - β × EFE(a))"
                color={COLORS.efe}
                width={300}
                height={120}
              />
              <div className="text-xs mt-2 p-2 rounded" style={{ backgroundColor: COLORS.bg, color: COLORS.textMuted }}>
                <div>Sum: {actionPosterior.reduce((a, b) => a + b, 0).toFixed(6)}</div>
                <div className="mt-1">Non-zero actions: {actionPosterior.filter(p => p > 0).length} / {actions.length}</div>
              </div>
            </Section>
            
            <Section title="Actions" defaultOpen={true}>
              <ActionEvaluationPanel
                actions={actions}
                efeValues={efeValues}
                optimalAction={optimalAction}
                actionPrior={actionPrior}
                actionPosterior={actionPosterior}
                onActionClick={executeAction}
                onSampleAction={sampleAndExecuteAction}
              />
            </Section>
            
            <Section title="Gridworld Controls" defaultOpen={false}>
              <button
                onClick={resetGridworld}
                className="w-full px-3 py-2 rounded text-sm font-medium transition-colors"
                style={{ backgroundColor: COLORS.border, color: COLORS.text }}
              >
                Reset Gridworld
              </button>
            </Section>
          </div>
        </div>
        
        {/* Right: Visualizations */}
        <div className="flex-1 space-y-2">
          <Section title="Gridworld" defaultOpen={true} hint="click tiles to inspect beliefs">
            <div className="flex flex-wrap gap-4 items-start">
              <div>
                <GridworldVisualization
                  gridworld={gridworld}
                  agentPos={agentPos}
                  visitedTiles={visitedTiles}
                  selectedTile={selectedTile}
                  onTileClick={setSelectedTile}
                  width={400}
                  height={400}
                />
                <div className="text-xs mt-2 text-center" style={{ color: COLORS.textDim }}>
                  Click any tile to view its belief distribution
                </div>
              </div>
              <div className="text-xs space-y-3 flex-1 min-w-[200px]">
                <div>
                  <div className="font-medium mb-2" style={{ color: COLORS.textMuted }}>
                    <strong>Tile Visualization:</strong>
                  </div>
                  <div className="space-y-1" style={{ color: COLORS.textDim }}>
                    <div>• <span style={{ color: TEMP_COLORS['Hot'] }}>Top-left triangle</span> = Temperature</div>
                    <div>• <span style={{ color: PH_COLORS['Basic'] }}>Bottom-right triangle</span> = pH</div>
                    <div>• Letters: <strong>T</strong> (Temp) / <strong>P</strong> (pH) abbreviations</div>
                  </div>
                </div>
                
                <div>
                  <div className="font-medium mb-2" style={{ color: COLORS.textMuted }}>
                    <strong>Temperature Colors:</strong>
                  </div>
                  <div className="space-y-1" style={{ color: COLORS.textDim }}>
                    {Object.entries(TEMP_COLORS).map(([temp, color]) => (
                      <div key={temp}>
                        <span style={{ color }}>■</span> {temp}
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <div className="font-medium mb-2" style={{ color: COLORS.textMuted }}>
                    <strong>pH Colors:</strong>
                  </div>
                  <div className="space-y-1" style={{ color: COLORS.textDim }}>
                    {Object.entries(PH_COLORS).map(([pH, color]) => (
                      <div key={pH}>
                        <span style={{ color }}>■</span> {pH}
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <div className="font-medium mb-2" style={{ color: COLORS.textMuted }}>
                    <strong>Indicators:</strong>
                  </div>
                  <div className="space-y-1" style={{ color: COLORS.textDim }}>
                    <div style={{ color: COLORS.agent }}>● Agent position</div>
                    <div style={{ color: COLORS.visited }}>● Visited tiles (small dot)</div>
                    <div style={{ color: COLORS.efe }}>■ Selected tile (highlighted border)</div>
                  </div>
                </div>
                
                {selectedTile && (
                  <div className="mt-3 p-2 rounded border" style={{ backgroundColor: COLORS.panel, borderColor: COLORS.efe }}>
                    <div className="font-medium mb-1" style={{ color: COLORS.textMuted }}>Selected Tile:</div>
                    <div>Position: ({selectedTile.row}, {selectedTile.col})</div>
                    <div>Temperature: <span style={{ color: TEMP_COLORS[selectedTile.temperature] }}>{selectedTile.temperature}</span></div>
                    <div>pH: <span style={{ color: PH_COLORS[selectedTile.pH] }}>{selectedTile.pH}</span></div>
                    <div className="mt-2 text-xs" style={{ color: COLORS.textDim }}>
                      View belief distribution in the "Belief Distributions" section below.
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Section>
          
          <Section title="Preference Distributions" defaultOpen={true}>
            <div className="flex flex-wrap gap-4">
              <div>
                <div className="text-xs mb-2" style={{ color: COLORS.temperature }}>Temperature Preference</div>
                <PreferenceDistributionPlot
                  categories={TEMPERATURE_CATEGORIES}
                  preference={tempPreference}
                  width={300}
                  height={150}
                />
              </div>
              <div>
                <div className="text-xs mb-2" style={{ color: COLORS.pH }}>pH Preference</div>
                <PreferenceDistributionPlot
                  categories={PH_CATEGORIES}
                  preference={pHPreference}
                  width={300}
                  height={150}
                />
              </div>
            </div>
          </Section>
          
          <Section title="Uncertainty Heatmap" defaultOpen={true} hint="click tiles to select - entropy over gridworld">
            <div className="flex flex-wrap gap-4 items-start">
              <div>
                <UncertaintyHeatmap 
                beliefs={beliefs} 
                gridworld={gridworld}
                selectedTile={selectedTile}
                onTileClick={setSelectedTile}
                width={400} 
                height={400} 
              />
                <div className="text-xs mt-2 text-center" style={{ color: COLORS.textDim }}>
                  Click any tile to view its belief distribution
                </div>
              </div>
              <div className="text-xs space-y-2 flex-1 min-w-[200px]" style={{ color: COLORS.textMuted }}>
                <div className="font-medium mb-2">Legend:</div>
                <p><span style={{ color: '#FF0000' }}>Red</span> = high uncertainty (unvisited tiles)</p>
                <p><span style={{ color: '#00FF00' }}>Green</span> = low uncertainty (visited tiles)</p>
                <p className="mt-3">Epistemic value measures expected reduction in this uncertainty.</p>
                <p className="mt-2 p-2 rounded" style={{ backgroundColor: COLORS.bg, color: COLORS.textDim }}>
                  <strong>Tip:</strong> Clicking a tile here will select it for belief inspection.
                </p>
              </div>
            </div>
          </Section>
          
          <Section title="Belief Distributions" defaultOpen={true} hint="select a tile to inspect">
            <div className="space-y-3">
              <div className="text-xs p-2 rounded" style={{ backgroundColor: COLORS.panel, color: COLORS.textMuted }}>
                <div className="font-medium mb-1">How to select a tile:</div>
                <ul className="list-disc list-inside space-y-1" style={{ color: COLORS.textDim }}>
                  <li>Click any tile in the Gridworld visualization</li>
                  <li>Click any tile in the Uncertainty Heatmap</li>
                  <li>Use the tile selector below</li>
                </ul>
              </div>
              
              {/* Tile Selector */}
              <div className="p-2 rounded border" style={{ backgroundColor: COLORS.bg, borderColor: COLORS.border }}>
                <div className="text-xs mb-2" style={{ color: COLORS.textMuted }}>Manual Tile Selection:</div>
                <div className="flex items-center gap-2 flex-wrap">
                  <label className="text-xs" style={{ color: COLORS.textDim }}>Row:</label>
                  <input
                    type="number"
                    min={0}
                    max={GRID_SIZE - 1}
                    value={selectedTile?.row ?? Math.floor(GRID_SIZE / 2)}
                    onChange={(e) => {
                      const row = parseInt(e.target.value) || 0;
                      const col = selectedTile?.col ?? Math.floor(GRID_SIZE / 2);
                      const tile = getTile(gridworld, row, col);
                      if (tile) setSelectedTile(tile);
                    }}
                    className="w-16 px-2 py-1 rounded text-xs"
                    style={{ backgroundColor: COLORS.panel, color: COLORS.text, border: `1px solid ${COLORS.border}` }}
                  />
                  <label className="text-xs" style={{ color: COLORS.textDim }}>Col:</label>
                  <input
                    type="number"
                    min={0}
                    max={GRID_SIZE - 1}
                    value={selectedTile?.col ?? Math.floor(GRID_SIZE / 2)}
                    onChange={(e) => {
                      const col = parseInt(e.target.value) || 0;
                      const row = selectedTile?.row ?? Math.floor(GRID_SIZE / 2);
                      const tile = getTile(gridworld, row, col);
                      if (tile) setSelectedTile(tile);
                    }}
                    className="w-16 px-2 py-1 rounded text-xs"
                    style={{ backgroundColor: COLORS.panel, color: COLORS.text, border: `1px solid ${COLORS.border}` }}
                  />
                  <button
                    onClick={() => setSelectedTile(null)}
                    className="px-2 py-1 rounded text-xs transition-colors"
                    style={{ backgroundColor: COLORS.border, color: COLORS.text }}
                  >
                    Clear
                  </button>
                </div>
              </div>
              
              {selectedTile ? (
                <div>
                  <div className="text-xs mb-2 p-2 rounded" style={{ backgroundColor: COLORS.panel, color: COLORS.textMuted }}>
                    <div className="font-medium">Selected Tile: ({selectedTile.row}, {selectedTile.col})</div>
                    <div className="mt-1" style={{ color: COLORS.textDim }}>
                      Temperature: <span style={{ color: TEMP_COLORS[selectedTile.temperature] }}>{selectedTile.temperature}</span> | 
                      pH: <span style={{ color: PH_COLORS[selectedTile.pH] }}>{selectedTile.pH}</span>
                    </div>
                  </div>
                  <BeliefDistribution beliefs={beliefs} tile={selectedTile} width={300} height={200} />
                </div>
              ) : (
                <div className="text-xs p-3 rounded text-center" style={{ backgroundColor: COLORS.panel, color: COLORS.textDim }}>
                  No tile selected. Use one of the methods above to select a tile.
                </div>
              )}
            </div>
          </Section>
          
          <Section title="EFE Numerical Values" defaultOpen={true} hint="exact values with dynamic sizing">
            <EFENumericalDisplay
              actions={actions}
              efeValues={efeValues}
              optimalAction={optimalAction}
            />
          </Section>
          
          <Section title="EFE Equation" defaultOpen={true} hint="mathematical framework">
            <div className="space-y-3 text-sm">
              <div className="rounded p-3" style={{ backgroundColor: COLORS.bg }}>
                <div className="font-mono text-center mb-2" style={{ color: COLORS.text }}>
                  <V type="efe">EFE(a)</V> = <V type="pragmatic">Pragmatic(a)</V> + <V type="epistemic">Epistemic(a)</V>
                </div>
                <div className="text-xs space-y-1" style={{ color: COLORS.textMuted }}>
                  <div><strong>Pragmatic Value:</strong> D<Sub>KL</Sub>[P(o|a) || C(o)]</div>
                  <div style={{ color: COLORS.textDim }}>
                    Measures alignment with preference distributions. Lower = better.
                  </div>
                  <div className="mt-2"><strong>Epistemic Value:</strong> E[H[P(s|o,a)]] - H[P(s)]</div>
                  <div style={{ color: COLORS.textDim }}>
                    Measures expected information gain. Higher = more exploration.
                  </div>
                  <div className="mt-2" style={{ color: COLORS.text }}>
                    <strong>Action Selection:</strong> Minimize EFE to balance preference satisfaction and information gathering.
                  </div>
                </div>
              </div>
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}
