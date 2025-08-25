# English Platform (Initial Scaffold)

This is an initial scaffold generated from the Figma reference. Flesh out sections and components as the design evolves.

## Stack
- Vite + React 18 + TypeScript
- React Router DOM for routing
- CSS variables + handcrafted utility styles (`src/styles/global.css`)

## Scripts
- `npm run dev` – start dev server
- `npm run build` – type check then build
- `npm run preview` – preview production build

## Structure
```
src/
  main.tsx            # App entry
  pages/              # Route-level pages
  components/layout   # Layout chrome (NavBar, Footer, MainLayout)
  styles/global.css   # Design tokens & base styles
```

## Next Steps
- Replace placeholder copy & sections according to Figma.
- Add responsive nav collapse (mobile menu button).
- Extract design tokens to separate `tokens.css` if they grow.
- Introduce ESLint + Prettier.
- Add testing (Vitest + React Testing Library).
- Implement state management if needed (Zustand, Redux, or Context API).

## Running Locally
Install dependencies then start dev server.

```
npm install
npm run dev
```

Open http://localhost:5173

## Deployment
Build the site, then deploy the `dist/` folder (e.g., GitHub Pages, Netlify, Vercel).

```
npm run build
```

## License
TBD
