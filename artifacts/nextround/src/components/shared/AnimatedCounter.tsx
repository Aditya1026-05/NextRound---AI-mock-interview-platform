import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface AnimatedCounterProps {
  value: number;
  duration?: number;
  className?: string;
}

export function AnimatedCounter({ value, className }: AnimatedCounterProps) {
  const [displayValue, setDisplayValue] = useState(value);

  useEffect(() => {
    let start = displayValue;
    const end = value;
    if (start === end) return;

    const totalDuration = 600; // ms
    const startTime = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / totalDuration, 1);
      
      // Easing curve (easeOutQuad)
      const ease = progress * (2 - progress);
      const current = Math.round(start + (end - start) * ease);
      
      setDisplayValue(current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [value]);

  // Render individual digits with Framer Motion slide animation on change
  const digits = displayValue.toString().split('');

  return (
    <div className={`flex overflow-hidden font-mono ${className}`}>
      {digits.map((digit, index) => (
        <span key={index} className="inline-block relative">
          <AnimatePresence mode="popLayout">
            <motion.span
              key={digit}
              initial={{ y: 15, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -15, opacity: 0 }}
              transition={{ duration: 0.18, ease: 'easeOut' }}
              className="inline-block"
            >
              {digit}
            </motion.span>
          </AnimatePresence>
        </span>
      ))}
    </div>
  );
}
export default AnimatedCounter;
