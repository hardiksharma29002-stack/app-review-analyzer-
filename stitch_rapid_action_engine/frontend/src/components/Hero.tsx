"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { Loader2, UploadCloud, Download } from "lucide-react";

export default function Hero({ onGenerate }: { onGenerate: (file: File | null) => void }) {
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const uploadRef = useRef<HTMLDivElement>(null);
  
  const [isHovered, setIsHovered] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    const tl = gsap.timeline();

    // Reveal title letter by letter
    if (titleRef.current) {
      const chars = titleRef.current.innerText.split("");
      titleRef.current.innerText = "";
      chars.forEach((char) => {
        const span = document.createElement("span");
        span.innerText = char === " " ? "\u00A0" : char;
        span.style.opacity = "0";
        span.style.display = "inline-block";
        titleRef.current?.appendChild(span);
      });

      tl.to(titleRef.current.children, {
        opacity: 1,
        y: 0,
        rotateX: 0,
        stagger: 0.03,
        duration: 0.8,
        ease: "power3.out",
        startAt: { y: 20, rotateX: 90 },
      });
    }

    tl.fromTo(
      subtitleRef.current,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" },
      "-=0.4"
    );

    tl.fromTo(
      buttonRef.current,
      { opacity: 0, scale: 0.9 },
      { opacity: 1, scale: 1, duration: 0.8, ease: "elastic.out(1, 0.5)" },
      "-=0.6"
    );
    
    tl.fromTo(
      uploadRef.current,
      { opacity: 0, y: 10 },
      { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" },
      "-=0.4"
    );
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setError(null);
      
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith('.csv')) {
        setError("Please upload a valid CSV file.");
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleRunAnalysis = () => {
    setIsGenerating(true);
    setTimeout(() => { 
      setIsGenerating(false); 
      onGenerate(selectedFile); 
    }, 1000);
  };

  return (
    <section className="relative flex flex-col items-center justify-center min-h-screen px-4 text-center z-10 pt-20">
      <div className="absolute top-8 left-8 text-2xl font-bold tracking-tighter text-foreground/90">
        App Review <span className="text-primary">Insights</span>
      </div>

      <h1 
        ref={titleRef}
        className="text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-tight mb-6 max-w-5xl leading-tight"
        style={{ perspective: "1000px" }}
      >
        Turn User Reviews Into Product Strategy.
      </h1>
      
      <p 
        ref={subtitleRef}
        className="text-xl md:text-2xl text-foreground/60 mb-12 max-w-2xl font-light tracking-wide"
      >
        Discover exactly what your users love and hate in seconds. Experience an AI-powered insights engine like never before.
      </p>

      <button
        ref={buttonRef}
        onClick={handleRunAnalysis}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`relative group overflow-hidden rounded-full px-12 py-5 text-lg font-bold transition-all duration-300 ${
          selectedFile 
            ? "bg-primary text-white shadow-[0_0_30px_rgba(0,208,156,0.5)] hover:scale-105" 
            : "neumorphic-btn text-foreground"
        }`}
      >
        <div className="relative z-10 flex items-center gap-3">
          {isGenerating && <Loader2 className="animate-spin" size={20} />}
          <span>{isGenerating ? "Analyzing Data..." : "Run Analysis"}</span>
        </div>
        
        {/* Glow effect on hover */}
        <div 
          className="absolute inset-0 bg-primary/10 rounded-full blur-xl transition-opacity duration-300 opacity-0 group-hover:opacity-100"
        />
        
        {/* Border pulse */}
        <div className="absolute inset-0 rounded-full border border-primary/30 group-hover:border-primary group-hover:shadow-[0_0_20px_rgba(0,208,156,0.4)] transition-all duration-500" />
      </button>

      <div ref={uploadRef} className="mt-8 flex flex-col items-center">
        <span className="text-sm text-foreground/40 mb-3 font-medium uppercase tracking-widest">Or Analyze Custom Data</span>
        
        {error && <div className="text-red-400 mb-4 text-sm font-medium">{error}</div>}

        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center w-full max-w-sm md:max-w-none">
          <label className="cursor-pointer group relative flex items-center justify-center w-full md:w-64 h-14 rounded-2xl glass border border-foreground/10 hover:border-primary/50 transition-colors">
            <input type="file" className="hidden" onChange={handleUpload} />
            <div className="flex items-center gap-3 text-foreground/70 group-hover:text-primary transition-colors">
              <UploadCloud size={18} />
              <span className="font-semibold text-sm truncate max-w-[150px]">
                {selectedFile ? selectedFile.name : "Upload CSV File"}
              </span>
            </div>
          </label>
          
          <a 
            href="/sample_reviews.csv" 
            download
            className="group relative flex items-center justify-center w-full md:w-64 h-14 rounded-2xl glass border border-foreground/10 hover:border-primary/50 transition-colors"
          >
            <div className="flex items-center gap-3 text-foreground/70 group-hover:text-primary transition-colors">
              <Download size={18} />
              <span className="font-semibold text-sm">Download Sample CSV</span>
            </div>
          </a>
        </div>
      </div>
    </section>
  );
}
