"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Info, X, FileText, Upload, Sparkles } from "lucide-react";

export default function InstructionModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed top-8 right-24 z-[50] p-3 rounded-full glass hover:scale-110 transition-transform duration-300 flex items-center justify-center gap-2 group"
        aria-label="How to use"
      >
        <Info size={24} className="text-foreground" />
        <span className="max-w-0 overflow-hidden whitespace-nowrap group-hover:max-w-xs transition-all duration-300 ease-in-out text-foreground font-semibold px-0 group-hover:px-2">
          How to use
        </span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-background/80 backdrop-blur-sm z-[60]"
            />
            
            <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 pointer-events-none">
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                className="w-full max-w-2xl glass bg-background/50 rounded-3xl p-8 border border-foreground/10 shadow-2xl pointer-events-auto relative overflow-hidden"
              >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-blue-500 to-primary" />
                
                <button 
                  onClick={() => setIsOpen(false)}
                  className="absolute top-6 right-6 p-2 rounded-full hover:bg-foreground/10 transition-colors"
                >
                  <X className="text-foreground/70" />
                </button>

                <h2 className="text-3xl font-bold mb-8 flex items-center gap-3">
                  <Sparkles className="text-primary" size={32} />
                  How to Use the Pulse Engine
                </h2>

                <div className="space-y-8">
                  <div className="flex gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center shrink-0">
                      <span className="text-primary font-bold text-xl">1</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold mb-2">Run the Built-In Dataset</h3>
                      <p className="text-foreground/70 leading-relaxed">
                        Click the glowing <strong>"Run AI Analysis on Sample Data"</strong> button to immediately see how the AI processes 1,000+ Google Play Store reviews, categorizes themes, and generates strategic product recommendations.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-blue-500/20 flex items-center justify-center shrink-0">
                      <span className="text-blue-500 font-bold text-xl">2</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold mb-2">Upload Your Own Data</h3>
                      <p className="text-foreground/70 leading-relaxed mb-4">
                        Want to analyze your own app? Upload a <code>.csv</code> file. The AI engine is dynamic and will adapt to any product context automatically.
                      </p>
                      
                      <div className="bg-foreground/5 p-4 rounded-xl border border-foreground/10">
                        <h4 className="font-semibold text-sm uppercase tracking-wider text-foreground/50 mb-3 flex items-center gap-2">
                          <FileText size={16} /> Required CSV Format
                        </h4>
                        <div className="grid grid-cols-3 gap-2 text-sm font-mono text-center">
                          <div className="bg-background/80 py-2 rounded border border-foreground/10">title</div>
                          <div className="bg-background/80 py-2 rounded border border-foreground/10">text</div>
                          <div className="bg-background/80 py-2 rounded border border-foreground/10">rating</div>
                        </div>
                        <p className="text-xs text-foreground/50 mt-3 italic">Note: standard Google Play Store scraper formats (content, score) are also accepted.</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-8 pt-6 border-t border-foreground/10 flex justify-end">
                  <button 
                    onClick={() => setIsOpen(false)}
                    className="neumorphic-btn px-8 py-3 rounded-xl font-bold"
                  >
                    Got it!
                  </button>
                </div>
              </motion.div>
            </div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
