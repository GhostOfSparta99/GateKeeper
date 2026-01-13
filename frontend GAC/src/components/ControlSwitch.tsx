import { motion } from 'framer-motion';
import { Lock, Unlock } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

interface ControlSwitchProps {
  isLocked: boolean;
  onToggle: () => void;
}

export function ControlSwitch({ isLocked, onToggle }: ControlSwitchProps) {
  const { theme } = useTheme();

  return (
    <div className="flex flex-col items-center gap-4">
      <div
        className={`text-xs uppercase tracking-widest font-mono ${
          theme === 'stealth' ? 'text-gray-500' : 'text-gray-600'
        }`}
      >
        Access Control
      </div>

      <motion.button
        onClick={onToggle}
        className={`relative w-32 h-16 rounded-full p-1 transition-colors duration-300 ${
          isLocked
            ? theme === 'stealth'
              ? 'bg-red-950 border-2 border-red-500'
              : 'bg-red-100 border-2 border-red-600'
            : theme === 'stealth'
            ? 'bg-emerald-950 border-2 border-emerald-500'
            : 'bg-emerald-100 border-2 border-emerald-600'
        }`}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <motion.div
          className={`h-full aspect-square rounded-full flex items-center justify-center ${
            isLocked
              ? theme === 'stealth'
                ? 'bg-red-500'
                : 'bg-red-600'
              : theme === 'stealth'
              ? 'bg-emerald-500'
              : 'bg-emerald-600'
          }`}
          animate={{
            x: isLocked ? 64 : 0
          }}
          transition={{
            type: "spring",
            stiffness: 500,
            damping: 30
          }}
          style={{
            boxShadow: isLocked
              ? theme === 'stealth'
                ? '0 0 20px rgba(239, 68, 68, 0.6)'
                : '0 0 15px rgba(220, 38, 38, 0.4)'
              : theme === 'stealth'
              ? '0 0 20px rgba(16, 185, 129, 0.6)'
              : '0 0 15px rgba(22, 163, 74, 0.4)'
          }}
        >
          <motion.div
            key={isLocked ? 'locked' : 'unlocked'}
            initial={{ rotate: -180, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            {isLocked ? (
              <Lock className="w-6 h-6 text-white" />
            ) : (
              <Unlock className="w-6 h-6 text-white" />
            )}
          </motion.div>
        </motion.div>
      </motion.button>

      <div
        className={`text-sm font-mono ${
          isLocked
            ? theme === 'stealth'
              ? 'text-red-400'
              : 'text-red-600'
            : theme === 'stealth'
            ? 'text-emerald-400'
            : 'text-emerald-600'
        }`}
      >
        {isLocked ? '[ LOCKED ]' : '[ UNLOCKED ]'}
      </div>
    </div>
  );
}
