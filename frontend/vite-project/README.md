# DeepGuard AI — DeepFake Video Detection System

A React + Vite frontend for an AI-powered deepfake video detection system.

## Features

- **Hero** — animated landing section with CTA buttons
- **Upload & Detection** — drag-and-drop video upload with simulated AI analysis, result card with heatmap overlay and suspicious-frames timeline
- **Dashboard** — stat cards, detection history bar+line chart, real vs. fake doughnut chart (Chart.js)
- **Features** — six core architecture cards (CNN, LSTM, Attention, etc.)
- Smooth scroll navigation with active-link highlighting
- Fully responsive layout

## Tech Stack

- React 18
- Vite 5
- Chart.js 4 (via `chart.js/auto`)
- Sora + JetBrains Mono (Google Fonts)

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
deepguard-vite/
├── index.html
├── vite.config.js
├── package.json
├── public/
│   └── favicon.svg
└── src/
    ├── main.jsx       # Entry point
    ├── index.css      # Global reset, tokens, keyframes
    ├── App.css        # Component styles
    └── App.jsx        # All components (Navbar, Hero, Upload, Dashboard, Features)
```

## Notes

- The upload and analysis flow is **simulated** — wire up the `runAnalysis` function in `UploadSection` to your real backend API (`/api/analyze`).
- Chart.js is imported via `chart.js/auto` using dynamic `import()` to avoid any SSR issues.
