import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon, Shield } from 'lucide-react';
import { useTheme } from './contexts/ThemeContext';
import { StatusRing } from './components/StatusRing';
import { ControlSwitch } from './components/ControlSwitch';
import { LiveTerminal } from './components/LiveTerminal';

function App() {
  const { theme, toggleTheme } = useTheme();
  const [isLocked, setIsLocked] = useState(false);

  return (
    <div
      className={`min-h-screen transition-colors duration-500 ${
        theme === 'stealth'
          ? 'bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950'
          : 'bg-gradient-to-br from-gray-50 via-white to-gray-100'
      }`}
    >
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className={`absolute top-0 left-1/4 w-96 h-96 rounded-full blur-3xl opacity-20 ${
            isLocked
              ? 'bg-red-500'
              : 'bg-emerald-500'
          }`}
        />
        <div
          className={`absolute bottom-0 right-1/4 w-96 h-96 rounded-full blur-3xl opacity-20 ${
            theme === 'stealth' ? 'bg-cyan-500' : 'bg-blue-500'
          }`}
        />
      </div>

      <div className="relative z-10 min-h-screen flex flex-col">
        <header className="p-6">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <motion.div
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="flex items-center gap-3"
            >
              <Shield
                className={`w-8 h-8 ${
                  theme === 'stealth' ? 'text-cyan-400' : 'text-blue-600'
                }`}
              />
              <div>
                <h1
                  className={`text-2xl font-bold ${
                    theme === 'stealth' ? 'text-white' : 'text-gray-900'
                  }`}
                >
                  GATEKEEPER
                </h1>
                <p
                  className={`text-xs uppercase tracking-widest font-mono ${
                    theme === 'stealth' ? 'text-cyan-400' : 'text-blue-600'
                  }`}
                >
                  Command Interface
                </p>
              </div>
            </motion.div>

            <motion.button
              initial={{ x: 50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ duration: 0.5 }}
              onClick={toggleTheme}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                theme === 'stealth'
                  ? 'bg-cyan-950/30 border-cyan-500/30 text-cyan-400 hover:bg-cyan-950/50'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {theme === 'stealth' ? (
                <>
                  <Sun className="w-4 h-4" />
                  <span className="text-sm font-mono">Day Mode</span>
                </>
              ) : (
                <>
                  <Moon className="w-4 h-4" />
                  <span className="text-sm font-mono">Stealth Mode</span>
                </>
              )}
            </motion.button>
          </div>
        </header>

        <main className="flex-1 flex flex-col items-center justify-center px-6 pb-12 gap-12">
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <StatusRing isLocked={isLocked} />
          </motion.div>

          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <ControlSwitch
              isLocked={isLocked}
              onToggle={() => setIsLocked(!isLocked)}
            />
          </motion.div>

          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="w-full px-4"
          >
            <LiveTerminal />
          </motion.div>
        </main>

        <footer
          className={`p-4 text-center text-xs font-mono ${
            theme === 'stealth' ? 'text-gray-600' : 'text-gray-500'
          }`}
        >
          <p>Gatekeeper FS v1.0.0 | Remote Granular Access Control System</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
