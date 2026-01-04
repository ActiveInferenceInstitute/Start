🧠 Expected Free Energy: Gridworld Action Selection

An interactive React-based visualization of the EFE mathematical framework for action selection in a gridworld!

✨ Features:
• Gridworld with Temperature and pH attributes per tile (diagonal split visualization)
• Agent with uncertain beliefs about tile values
• Action evaluation via Pragmatic Value (preference alignment) + Epistemic Value (information gain)
• Interactive preference distribution controls
• Action prior and posterior distributions with EFE-weighted softmax
• Real-time EFE computation and visualization
• Belief uncertainty heatmaps and probability distributions
• Clickable tiles for belief inspection
• Action sampling from posterior distribution

🎬 Automated GIF Generation:
Run `npm run capture-gifs` to generate 7 animated demos showing:
- Preference slider movements
- Action execution and agent movement
- Tile selection and belief exploration
- Action prior adjustments
- Posterior visualization with beta parameter
- Section expansions/collapses
- Full interactive walkthrough

🚀 Quick Start:
```bash
cd examples/efe
npm install
npm run build
# Open efe-compiled.html in browser
```

Built with React, Tailwind CSS, following the VFE example style. Standalone HTML - no server needed! 🎯
