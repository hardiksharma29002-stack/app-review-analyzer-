"use client";

import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import SmoothScroll from "@/components/SmoothScroll";
import Canvas3D from "@/components/Canvas3D";
import Hero from "@/components/Hero";
import LoadingSequence from "@/components/LoadingSequence";
import ReportView from "@/components/ReportView";
import ThemeToggle from "@/components/ThemeToggle";
import InstructionModal from "@/components/InstructionModal";

export default function Home() {
  const [appState, setAppState] = useState<"hero" | "loading" | "report">("hero");
  const [reportData, setReportData] = useState<any>(null);
  const [isApiDone, setIsApiDone] = useState(false);
  const [isAnimationDone, setIsAnimationDone] = useState(false);

  useEffect(() => {
    if (isApiDone && isAnimationDone && appState === "loading") {
      setAppState("report");
    }
  }, [isApiDone, isAnimationDone, appState]);

  const handleGenerate = async (file: File | null) => {
    setAppState("loading");
    setIsApiDone(false);
    setIsAnimationDone(false);
    
    try {
      let res;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      if (file) {
        // Fix for Mobile OS (Android/iOS) file reading issues with fetch
        // Forces the browser to load the file into memory first
        const arrayBuffer = await file.arrayBuffer();
        const blob = new Blob([arrayBuffer], { type: file.type || 'text/csv' });
        
        const formData = new FormData();
        formData.append("file", blob, file.name);
        
        res = await fetch(`${apiUrl}/analyze/upload`, {
          method: "POST",
          body: formData,
        });
      } else {
        res = await fetch(`${apiUrl}/analyze`, {
          method: "POST",
        });
      }
      
      if (!res.ok) {
        const errText = await res.text();
        console.error("Backend error detail:", errText);
        throw new Error(`Failed to analyze: ${errText}`);
      }
      const data = await res.json();
      setReportData(data);
    } catch (e: any) {
      console.error("API error:", e);
      alert(e.message);
      setAppState("hero"); // Return to hero screen to let user try again
      setReportData(null);
    } finally {
      setIsApiDone(true);
    }
  };

  return (
    <SmoothScroll>
      <main className="relative min-h-screen">
        {/* Persistent interactive background */}
        <Canvas3D />
        <ThemeToggle />
        <InstructionModal />

        <AnimatePresence mode="wait">
          {appState === "hero" && (
            <motion.div
              key="hero"
              exit={{ opacity: 0, scale: 0.95, filter: "blur(10px)" }}
              transition={{ duration: 0.8 }}
            >
              <Hero onGenerate={handleGenerate} />
            </motion.div>
          )}

          {appState === "loading" && (
            <LoadingSequence 
              key="loading" 
              onComplete={() => setIsAnimationDone(true)} 
            />
          )}

          {appState === "report" && (
            <motion.div
              key="report"
              initial={{ opacity: 0, y: 100 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, ease: "easeOut" }}
            >
              <ReportView data={reportData} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </SmoothScroll>
  );
}
