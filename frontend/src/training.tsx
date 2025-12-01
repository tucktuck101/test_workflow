import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';
import { TrainingControl } from './TrainingControl';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div className="app-shell">
      <header className="header">
        <div>
          <div className="title">Trainer Control</div>
          <div className="status-line">
            Manage training runs. Back to{' '}
            <a href={import.meta.env.VITE_GAME_UI_URL || '/'}>Game UI</a>
          </div>
        </div>
      </header>
      <TrainingControl />
    </div>
  </React.StrictMode>
);
