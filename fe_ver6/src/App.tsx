/**
 * Main App component
 */

import { ChatProvider } from './context/ChatContext';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { SearchPanel } from './components/search/SearchPanel';
import { ChatInterface } from './components/chat/ChatInterface';
import { HistoryPanel } from './components/history/HistoryPanel';
import { PopularProcedures } from './components/procedures/PopularProcedures';
import './App.css';

function App() {
  return (
    <ChatProvider>
      <div className="app">
        <Header />

        <main className="main-content">
          <aside className="sidebar-left">
            <HistoryPanel />
          </aside>

          <section className="content-center">
            <SearchPanel />
            <ChatInterface />
          </section>

          <aside className="sidebar-right">
            <PopularProcedures />
          </aside>
        </main>

        <Footer />
      </div>
    </ChatProvider>
  );
}

export default App;
