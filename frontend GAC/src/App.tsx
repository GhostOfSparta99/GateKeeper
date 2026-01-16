import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, FileText, Lock, Unlock } from 'lucide-react';
import { useTheme } from './contexts/ThemeContext';
import { supabase } from './lib/supabase';

// Data Type for our files
interface FileNode {
  id: number;
  filename: string;
  is_locked: boolean;
  last_accessed: string | null;
}

function App() {
  const { theme, toggleTheme } = useTheme();
  const [files, setFiles] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(true);

  // 1. Fetch Files & Subscribe to Realtime Updates
  useEffect(() => {
    fetchFiles();

    const channel = supabase
      .channel('file_updates')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'file_locks' },
        (payload) => {
          // Refresh list on any change
          fetchFiles();
        }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, []);

  async function fetchFiles() {
    const { data } = await supabase.from('file_locks').select('*').order('filename');
    if (data) setFiles(data);
    setLoading(false);
  }

  // 2. Toggle Function
  const toggleLock = async (id: number, currentStatus: boolean) => {
    // Optimistic Update (update UI instantly)
    setFiles(files.map(f => f.id === id ? { ...f, is_locked: !currentStatus } : f));

    // Send to DB
    await supabase.from('file_locks').update({ is_locked: !currentStatus }).eq('id', id);
  };

  return (
    <div className={`min-h-screen transition-colors duration-500 ${theme === 'stealth' ? 'bg-gray-950 text-white' : 'bg-gray-50 text-gray-900'
      }`}>

      {/* Header */}
      <header className="p-6 border-b border-white/10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className={theme === 'stealth' ? 'text-emerald-500' : 'text-blue-600'} />
            <h1 className="text-xl font-bold tracking-wider">GATEKEEPER <span className="opacity-50 text-sm">| S: DRIVE MANAGER</span></h1>
          </div>
          <button onClick={toggleTheme} className="text-xs font-mono opacity-60 hover:opacity-100">
            SWITCH THEME
          </button>
        </div>
      </header>

      {/* Main File Grid */}
      <main className="max-w-4xl mx-auto p-6 mt-8">
        {loading ? (
          <div className="text-center animate-pulse font-mono">SCANNING DRIVE...</div>
        ) : (
          <div className="grid gap-4">
            <AnimatePresence>
              {files.map((file) => (
                <motion.div
                  key={file.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`p-4 rounded-xl border flex items-center justify-between transition-all ${file.is_locked
                      ? 'border-red-500/30 bg-red-500/5'
                      : 'border-emerald-500/30 bg-emerald-500/5'
                    } ${theme !== 'stealth' && 'bg-white shadow-sm'}`}
                >
                  {/* File Info */}
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-lg ${file.is_locked ? 'bg-red-500/20 text-red-500' : 'bg-emerald-500/20 text-emerald-500'}`}>
                      <FileText size={24} />
                    </div>
                    <div>
                      <h3 className="font-mono font-bold text-lg">{file.filename}</h3>
                      <p className="text-xs opacity-50 font-mono">
                        {file.is_locked ? 'ACCESS DENIED' : 'wkspc: S:/' + file.filename}
                      </p>
                    </div>
                  </div>

                  {/* Toggle Switch */}
                  <button
                    onClick={() => toggleLock(file.id, file.is_locked)}
                    className={`relative w-16 h-8 rounded-full transition-colors duration-300 flex items-center px-1 ${file.is_locked ? 'bg-red-500' : 'bg-emerald-500'
                      }`}
                  >
                    <motion.div
                      className="w-6 h-6 bg-white rounded-full shadow-md flex items-center justify-center"
                      animate={{ x: file.is_locked ? 32 : 0 }}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    >
                      {file.is_locked ? <Lock size={12} className="text-red-500" /> : <Unlock size={12} className="text-emerald-500" />}
                    </motion.div>
                  </button>

                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}

        {files.length === 0 && !loading && (
          <div className="text-center opacity-50 font-mono mt-10">
            NO FILES DETECTED IN S: DRIVE
            <br />
            <span className="text-xs">Add files to 'my_hidden_data' and restart Python script</span>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
