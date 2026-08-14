"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import gsap from "gsap";

const loadingTexts = [
  "Initializing AI Engine...",
  "Analyzing Reviews...",
  "Understanding Customers...",
  "Detecting Patterns...",
  "Removing Noise...",
  "Generating Intelligence...",
  "Building Product Pulse..."
];

export default function LoadingSequence({ onComplete }: { onComplete: () => void }) {
  const [textIndex, setTextIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Cycle text every 1.2s
    const interval = setInterval(() => {
      setTextIndex((prev) => {
        if (prev === loadingTexts.length - 1) {
          clearInterval(interval);
          setTimeout(onComplete, 1000);
          return prev;
        }
        return prev + 1;
      });
    }, 1200);

    // Initial cinematic entrance
    gsap.fromTo(
      containerRef.current,
      { backdropFilter: "blur(0px)", backgroundColor: "rgba(30, 30, 36, 0)" },
      { backdropFilter: "blur(20px)", backgroundColor: "rgba(10, 10, 15, 0.8)", duration: 1.5, ease: "power2.out" }
    );

    return () => clearInterval(interval);
  }, [onComplete]);

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center overflow-hidden"
    >
      {/* Central neural pulse animation */}
      <div className="relative w-64 h-64 flex items-center justify-center mb-12">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 8, ease: "linear" }}
          className="absolute inset-0 rounded-full border-t border-r border-primary/50 opacity-80"
          style={{ width: "100%", height: "100%" }}
        />
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ repeat: Infinity, duration: 12, ease: "linear" }}
          className="absolute inset-4 rounded-full border-b border-l border-white/30 opacity-60"
        />
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
          className="w-16 h-16 bg-primary rounded-full blur-xl"
        />
        <div className="absolute w-10 h-10 bg-background border border-primary/50 rounded-full shadow-[0_0_20px_#00D09C]" />
      </div>

      {/* Cycling text with AnimatePresence */}
      <div className="h-12 relative w-full flex justify-center">
        <AnimatePresence mode="wait">
          <motion.h2
            key={textIndex}
            initial={{ opacity: 0, y: 20, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -20, filter: "blur(10px)" }}
            transition={{ duration: 0.5, ease: "backOut" }}
            className="absolute text-3xl md:text-4xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-primary to-white"
          >
            {loadingTexts[textIndex]}
          </motion.h2>
        </AnimatePresence>
      </div>

      <motion.div 
        initial={{ width: 0 }}
        animate={{ width: "300px" }}
        transition={{ duration: 8, ease: "linear" }}
        className="mt-8 h-1 bg-primary rounded-full"
      />
    </div>
  );
}
