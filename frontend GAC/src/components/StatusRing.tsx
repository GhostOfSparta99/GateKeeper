import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';

interface StatusRingProps {
  isLocked: boolean;
}

export function StatusRing({ isLocked }: StatusRingProps) {
  const { theme } = useTheme();

  const ringColor = isLocked
    ? (theme === 'stealth' ? '#ef4444' : '#dc2626')
    : (theme === 'stealth' ? '#10b981' : '#16a34a');

  const glowColor = isLocked
    ? (theme === 'stealth' ? 'rgba(239, 68, 68, 0.5)' : 'rgba(220, 38, 38, 0.3)')
    : (theme === 'stealth' ? 'rgba(16, 185, 129, 0.5)' : 'rgba(22, 163, 74, 0.3)');

  const statusText = isLocked ? 'SECURE' : 'UNLOCKED';
  const statusLabel = isLocked ? 'System Locked' : 'System Safe';

  return (
    <div className="flex flex-col items-center justify-center">
      <motion.div
        className="relative flex items-center justify-center"
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <svg width="280" height="280" viewBox="0 0 280 280" className="transform -rotate-90">
          <circle
            cx="140"
            cy="140"
            r="120"
            fill="none"
            stroke={theme === 'stealth' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'}
            strokeWidth="2"
          />

          <motion.circle
            cx="140"
            cy="140"
            r="120"
            fill="none"
            stroke={ringColor}
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray="753.98"
            initial={{ strokeDashoffset: 753.98 }}
            animate={{ strokeDashoffset: 0 }}
            transition={{ duration: 1.5, ease: "easeInOut" }}
            style={{
              filter: `drop-shadow(0 0 12px ${glowColor})`
            }}
          />

          <motion.circle
            cx="140"
            cy="140"
            r="110"
            fill="none"
            stroke={ringColor}
            strokeWidth="1"
            opacity="0.4"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.8, delay: 0.3 }}
          />
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.div
            key={statusText}
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="text-center"
          >
            <div
              className="text-5xl font-bold mb-2 font-mono tracking-wider"
              style={{ color: ringColor }}
            >
              {statusText}
            </div>
            <div
              className={`text-sm uppercase tracking-widest ${
                theme === 'stealth' ? 'text-gray-400' : 'text-gray-600'
              }`}
            >
              {statusLabel}
            </div>
          </motion.div>
        </div>

        <motion.div
          className="absolute inset-0 rounded-full"
          animate={{
            boxShadow: [
              `0 0 20px ${glowColor}`,
              `0 0 40px ${glowColor}`,
              `0 0 20px ${glowColor}`
            ]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </motion.div>
    </div>
  );
}
