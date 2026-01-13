import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

interface TerminalLog {
  id: number;
  text: string;
  timestamp: string;
}

const logMessages = [
  '> Initializing Gatekeeper FS...',
  '> Connecting to secure channel...',
  '> Establishing encrypted link...',
  '> Agent handshake complete',
  '> Monitoring file system...',
  '> Awaiting instructions...',
  '> System status: NOMINAL',
  '> Heartbeat detected',
  '> Security protocols active',
  '> Standing by...'
];

export function LiveTerminal() {
  const { theme } = useTheme();
  const [logs, setLogs] = useState<TerminalLog[]>([]);
  const [currentText, setCurrentText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const message = logMessages[currentIndex % logMessages.length];
    let charIndex = 0;

    const typingInterval = setInterval(() => {
      if (charIndex <= message.length) {
        setCurrentText(message.slice(0, charIndex));
        charIndex++;
      } else {
        clearInterval(typingInterval);

        setTimeout(() => {
          const newLog: TerminalLog = {
            id: Date.now(),
            text: message,
            timestamp: new Date().toLocaleTimeString('en-US', { hour12: false })
          };

          setLogs(prev => {
            const updated = [...prev, newLog];
            return updated.slice(-5);
          });

          setCurrentText('');
          setCurrentIndex(prev => prev + 1);
        }, 500);
      }
    }, 50);

    return () => clearInterval(typingInterval);
  }, [currentIndex]);

  return (
    <div
      className={`w-full max-w-2xl mx-auto rounded-lg border ${
        theme === 'stealth'
          ? 'bg-black/40 border-cyan-500/30 backdrop-blur-sm'
          : 'bg-white border-gray-300'
      } overflow-hidden`}
    >
      <div
        className={`flex items-center gap-2 px-4 py-2 border-b ${
          theme === 'stealth'
            ? 'border-cyan-500/30 bg-cyan-950/20'
            : 'border-gray-300 bg-gray-100'
        }`}
      >
        <Terminal className={`w-4 h-4 ${theme === 'stealth' ? 'text-cyan-400' : 'text-gray-700'}`} />
        <span
          className={`text-xs font-mono uppercase tracking-wider ${
            theme === 'stealth' ? 'text-cyan-400' : 'text-gray-700'
          }`}
        >
          System Monitor
        </span>
        <div className="flex-1" />
        <div className="flex gap-1">
          <div className={`w-2 h-2 rounded-full ${theme === 'stealth' ? 'bg-emerald-500' : 'bg-emerald-600'}`} />
          <div className={`w-2 h-2 rounded-full ${theme === 'stealth' ? 'bg-cyan-500' : 'bg-blue-600'}`} />
        </div>
      </div>

      <div className="p-4 space-y-1 font-mono text-xs h-32 overflow-hidden">
        <AnimatePresence mode="popLayout">
          {logs.map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className={`flex gap-2 ${
                theme === 'stealth' ? 'text-emerald-400' : 'text-emerald-700'
              }`}
            >
              <span className={theme === 'stealth' ? 'text-gray-600' : 'text-gray-500'}>
                [{log.timestamp}]
              </span>
              <span>{log.text}</span>
            </motion.div>
          ))}
        </AnimatePresence>

        {currentText && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`flex gap-2 ${
              theme === 'stealth' ? 'text-cyan-400' : 'text-blue-700'
            }`}
          >
            <span className={theme === 'stealth' ? 'text-gray-600' : 'text-gray-500'}>
              [{new Date().toLocaleTimeString('en-US', { hour12: false })}]
            </span>
            <span>
              {currentText}
              <motion.span
                animate={{ opacity: [1, 0, 1] }}
                transition={{ duration: 0.8, repeat: Infinity }}
              >
                _
              </motion.span>
            </span>
          </motion.div>
        )}
      </div>
    </div>
  );
}
