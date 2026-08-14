import { useState, useRef } from "react";
import { Sun, Moon } from "lucide-react";
import gsap from "gsap";

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(true);
  const rippleRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const toggleTheme = (e: React.MouseEvent) => {
    const isNowDark = !isDark;
    
    // Get click coordinates for ripple origin
    const rect = buttonRef.current?.getBoundingClientRect();
    const x = rect ? rect.left + rect.width / 2 : e.clientX;
    const y = rect ? rect.top + rect.height / 2 : e.clientY;
    
    if (rippleRef.current) {
      // Set initial ripple state
      gsap.set(rippleRef.current, {
        x, 
        y, 
        scale: 0, 
        opacity: 1,
        backgroundColor: isNowDark ? "#1E1E24" : "#F3F4F6"
      });
      
      // Animate ripple to cover the entire screen
      // Calculate hypotenuse to ensure circle covers screen corners
      const maxDim = Math.max(window.innerWidth, window.innerHeight);
      
      gsap.to(rippleRef.current, {
        scale: (maxDim / 10) * 2.5, // Make it massive
        duration: 1.2,
        ease: "power3.inOut",
        onComplete: () => {
          setIsDark(isNowDark);
          if (isNowDark) {
            document.documentElement.classList.remove("light-mode");
          } else {
            document.documentElement.classList.add("light-mode");
          }
          // Fade out the fake ripple after the actual DOM updates
          gsap.to(rippleRef.current, { 
            opacity: 0, 
            duration: 0.5, 
            delay: 0.1,
            onComplete: () => gsap.set(rippleRef.current, { scale: 0 }) 
          });
        }
      });
    }
  };

  return (
    <>
      <div 
        ref={rippleRef} 
        className="fixed top-0 left-0 w-8 h-8 rounded-full pointer-events-none z-[40] -translate-x-1/2 -translate-y-1/2 opacity-0"
      />
      <button
        ref={buttonRef}
        onClick={toggleTheme}
        className="fixed top-8 right-8 z-[50] p-3 rounded-full glass hover:scale-110 transition-transform duration-300"
        aria-label="Toggle theme"
      >
        {isDark ? <Sun size={24} className="text-foreground" /> : <Moon size={24} className="text-foreground" />}
      </button>
    </>
  );
}
