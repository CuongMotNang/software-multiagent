import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { GrapesSpike } from './spike/GrapesSpike.tsx'

// SPIKE Bước 0: mount GrapesJS spike khi URL có ?spike=1,
// KHÔNG động tới App.tsx của Puck. Mặc định (không query param) vẫn render App.
const params = new URLSearchParams(window.location.search)
const isSpike = params.get('spike') === '1'

createRoot(document.getElementById('root')!).render(
  isSpike ? <GrapesSpike /> : <App />
)
